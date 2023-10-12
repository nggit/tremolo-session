# Copyright (c) 2023 nggit

__all__ = ('Session', 'SessionData')

import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402

from urllib.parse import parse_qs  # noqa: E402

from tremolo.exceptions import Forbidden  # noqa: E402


class Session:
    def __init__(self, app, name='sess', path='sess',
                 expires=1800, cookie_params={}):
        """A simple, file-based session middleware for Tremolo.

        :param app: The Tremolo app object
        :param name: Session name. Will be used in the response header. E.g.
            ``Set-Cookie: sess=id%3D0123456789abcdef%26expires%3D1234567890;``
        :param path: A session directory path where the session files will be
            stored. E.g. ``/path/to/dir``. If it doesn't exist, it will be
            created under the Operating System temporary directory.
        """
        self.name = name
        self.path = self._get_path(path)
        self.expires = min(expires, 31968000)

        # overwrite to maximum cookie validity (400 days)
        cookie_params['expires'] = 34560000

        self.cookie_params = cookie_params

        app.middlewares['request'].append((self._request_handler, {}))
        app.middlewares['response'].append((self._response_handler, {}))

    def _get_path(self, path):
        if os.path.exists(path):
            return path

        tmp = tempfile.mkdtemp()
        os.rmdir(tmp)
        _tmp = os.path.join(os.path.dirname(tmp),
                            'tremolo-%s' % os.path.basename(path))

        try:
            os.mkdir(_tmp)
        except FileExistsError:
            pass

        return _tmp

    def _regenerate_id(self, request, response):
        if request.client is None:
            port = request.socket.fileno()
        else:
            port = request.client[1]

        for i in range(2):
            session_id = hashlib.sha256(
                (b'%s:%d:%d:%f:%d:%s' % (request.ip,
                                         port,
                                         os.getpid(),
                                         time.time(),
                                         i,
                                         os.urandom(16)))[-63:]).hexdigest()

            if not os.path.exists(os.path.join(self.path, session_id)):
                return session_id

        raise FileExistsError('session id collision')

    def _set_cookie(self, response, session_id):
        response.set_cookie(
            self.name,
            'id=%s&expires=%d' % (session_id, int(time.time() + self.expires)),
            **self.cookie_params
        )

    async def _request_handler(self, request=None, response=None, **_):
        if self.name not in request.cookies:
            self._set_cookie(response, self._regenerate_id(request, response))

            request.context.session = None
            return

        try:
            sess = parse_qs(request.cookies[self.name][0])
            session_id = sess['id'][0]

            int(session_id, 16)

            if time.time() > int(sess['expires'][0]):
                try:
                    os.unlink(os.path.join(self.path, session_id))
                except FileNotFoundError:
                    pass
        except (KeyError, ValueError) as exc:
            raise Forbidden('bad cookie') from exc

        session = {}
        session_filepath = os.path.join(self.path, session_id)

        if os.path.exists(session_filepath):
            fp = open(session_filepath, 'r')

            try:
                session = json.loads(fp.read())
                fp.close()
            except ValueError:
                fp.close()
                os.unlink(session_filepath)

        if not os.path.exists(session_filepath):
            session_id = self._regenerate_id(request, response)
            session_filepath = os.path.join(self.path, session_id)

        request.context.session = SessionData(self.name,
                                              session_id,
                                              session,
                                              session_filepath,
                                              request)

        # always renew/update session and cookie expiration time
        self._set_cookie(response, session_id)

    async def _response_handler(self, context=None, **_):
        if context.session is not None:
            context.session.save()


class SessionData(dict):
    def __init__(self, name, session_id, session, filepath, request):
        self.name = name
        self.id = session_id
        self.session = session
        self.filepath = filepath
        self.request = request

        super().__init__()
        self.update(session)

    def save(self):
        if self != self.session:
            with open(self.filepath, 'w') as fp:
                json.dump(self, fp)

    def destroy(self):
        try:
            os.unlink(self.filepath)
        except FileNotFoundError:
            pass
