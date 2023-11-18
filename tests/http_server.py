#!/usr/bin/env python3

__all__ = ('app', 'HTTP_HOST', 'HTTP_PORT')

import json  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402

# makes imports relative from the repo directory
sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from tremolo import Tremolo  # noqa: E402
from tremolo_session import Session  # noqa: E402

HTTP_HOST = '127.0.0.1'
HTTP_PORT = 28000

app = Tremolo()

# session middleware
sess = Session(app)

session_filepath = os.path.join(sess.path, '5e55')


@app.on_worker_start
async def worker_start(**_):
    # create file /tmp/tremolo-sess/5e55
    with open(session_filepath, 'w') as fp:
        json.dump({'foo': 'bar'}, fp)

    # create file /tmp/tremolo-sess/5e55bad
    with open(session_filepath + 'bad', 'w') as fp:
        fp.write('{badfile}')


@app.route('/')
async def index(context=None, response=None, **_):
    if context.session is None:
        # there is no session because the client does not send 'sess' cookie
        return b'\r\n'.join(b'\r\n'.join(v) for v in response.headers.values())

    # set session
    context.session['baz'] = 'qux'
    return b'OK'


@app.on_response
async def my_response_middleware(request=None, response=None, **_):
    session = request.context.session

    if session is not None:
        assert session['baz'] == 'qux'

        if 'id=5e55&expires=' in request.cookies['sess'][0]:
            assert session['foo'] == 'bar'
            assert os.path.basename(session.filepath) == '5e55'

            # test idempotence
            session.destroy()
            session.destroy()

            assert os.path.exists(session.filepath) is False
        elif 'id=5e55bad&expires=' in request.cookies['sess'][0]:
            assert os.path.basename(session.filepath) != '5e55bad'

if __name__ == '__main__':
    app.run(HTTP_HOST, port=HTTP_PORT, debug=True)
