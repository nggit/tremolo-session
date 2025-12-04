#!/usr/bin/env python3

__all__ = ('app', 'HTTP_HOST', 'HTTP_PORT')

import json  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402

# makes imports relative from the repo directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tremolo import Application  # noqa: E402
from tremolo_session import Session  # noqa: E402

HTTP_HOST = '127.0.0.1'
HTTP_PORT = 28000

app = Application()

# session middleware
sess = Session(app, paths=['/cookies', '/invalid'])

session_filepath = os.path.join(sess.path, '5e55')


@app.on_worker_start
async def worker_start(**_):
    # create file /tmp/tremolo-sess/5e55
    with open(session_filepath, 'w') as fp:
        json.dump({'foo': 'bar'}, fp)

    # create file /tmp/tremolo-sess/5e55bad
    with open(session_filepath + 'bad', 'w') as fp:
        fp.write('{badfile}')


@app.route('/cookies')
async def index(request, response, **_):
    if request.ctx.session is None:
        # there is no session because the client does not send 'sess' cookie
        for values in list(response.headers.values()):
            for value in values:
                yield b'\r\n' + value
    else:
        # set session
        request.ctx.session['baz'] = 'qux'
        yield b'OK'


@app.on_response
async def response_middleware(request, response, **_):
    session = request.ctx.session

    if session is not None:
        assert session['baz'] == 'qux'

        if '5e55.' in request.cookies['sess'][0]:
            assert session['foo'] == 'bar'
            assert os.path.basename(session.filepath) == '5e55'

            # test idempotence
            session.delete()
            session.delete()

            assert os.path.exists(session.filepath) is False
        elif '5e55bad.' in request.cookies['sess'][0]:
            assert os.path.basename(session.filepath) != '5e55bad'


if __name__ == '__main__':
    app.run(HTTP_HOST, port=HTTP_PORT, debug=True)
