# SPDX-License-Identifier: MIT
# Copyright (c) 2023 Anggit Arfanto

import hashlib
import json
import os
import tempfile
import time

from tremolo.exceptions import Forbidden

__version__ = '1.0.12'
__all__ = ['Session', 'SessionData']


class Session:
    def __init__(self, app, name='sess', path='sess', paths=(),
                 expires=1800, cookie_params={}):
        """A simple, file-based session middleware for Tremolo.

        :param app: The Tremolo app object
        :param name: Session name. Will be used in the response header. E.g.
            ``Set-Cookie: sess=0123456789abcdef.1234567890;``
        :param path: A session directory path where the session files will be
            stored. E.g. ``/path/to/dir``. If it doesn't exist, it will be
            created under the Operating System temporary directory.
        :param paths: A list of url path prefixes
            where the ``Set-Cookie`` header should appear.
            ``['/']`` will match ``/any``,
            ``['/users']`` will match ``/users/login``, etc.
        """
        self.name = name
        self.path = self._get_path(path, app.__class__.__name__)
        self.paths = {v.rstrip('/').encode('latin-1') for v in paths}
        self.expires = min(expires, 31968000)

        # overwrite to maximum cookie validity (400 days)
        cookie_params['expires'] = 34560000

        self.cookie_params = cookie_params

        app.add_middleware(self._on_request, 'request')
        app.add_middleware(self._on_response, 'response')

    def _get_path(self, path, prefix):
        if os.path.isdir(path):
            return path

        tmp = tempfile.mkdtemp()
        os.rmdir(tmp)
        tmp = os.path.join(
            os.path.dirname(tmp), '%s-%s' % (prefix.lower(),
                                             os.path.basename(path))
        )

        if not os.path.exists(tmp):
            os.mkdir(tmp)

        return tmp

    def _regenerate_id(self, request, response):
        for i in range(2):
            session_id = hashlib.sha256(request.uid(32 + i)).hexdigest()

            if not os.path.exists(os.path.join(self.path, session_id)):
                return session_id

        raise FileExistsError('session id collision')

    def _set_cookie(self, response, session_id):
        response.set_cookie(
            self.name,
            '%s.%d' % (session_id, int(time.time() + self.expires)),
            **self.cookie_params
        )

    async def _on_request(self, request, response, **_):
        request.ctx.session = None
        path = request.path.rstrip(b'/')
        depth = 0

        while depth < 255:
            if not self.paths or path in self.paths:
                break

            end = path.rfind(b'/')

            if end == -1:
                return

            path = path[:end]
            depth += 1
        else:
            return

        response.set_header(b'Cache-Control', b'no-cache, must-revalidate')
        response.set_header(b'Expires', b'Thu, 01 Jan 1970 00:00:00 GMT')

        if self.name not in request.cookies:
            self._set_cookie(response, self._regenerate_id(request, response))
            return

        try:
            session_id, expires = request.cookies[self.name][0].split('.', 1)
            bytes.fromhex(session_id)

            expires = int(expires)
        except (KeyError, ValueError) as exc:
            self._set_cookie(response, self._regenerate_id(request, response))
            raise Forbidden('bad cookie') from exc

        session_filepath = os.path.join(self.path, session_id)
        session = {}

        if os.path.isfile(session_filepath):
            if time.time() > expires:
                os.unlink(session_filepath)
            else:
                fp = open(session_filepath, 'r')

                try:
                    session.update(json.loads(fp.read()))
                    fp.close()
                except ValueError:
                    fp.close()
                    os.unlink(session_filepath)

        if not os.path.isfile(session_filepath):
            session_id = self._regenerate_id(request, response)
            session_filepath = os.path.join(self.path, session_id)

        request.ctx.session = SessionData(self.name,
                                          session_id,
                                          session,
                                          session_filepath,
                                          request)

        # always renew/update session and cookie expiration time
        self._set_cookie(response, session_id)

    async def _on_response(self, request, **_):
        if request.ctx.session is not None:
            request.ctx.session.save()


class SessionData(dict):
    def __init__(self, name, session_id, session, filepath, request):
        self.name = name
        self.id = session_id
        self.session = session
        self.filepath = filepath
        self.request = request

        self.update(session)

    def save(self):
        if self != self.session:
            with open(self.filepath, 'w') as fp:
                json.dump(self, fp)

    def delete(self):
        if os.path.exists(self.filepath):
            os.unlink(self.filepath)
