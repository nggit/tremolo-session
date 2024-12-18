#!/usr/bin/env python3

from tremolo import Application
from tremolo_session import Session

app = Application()

# this is a session middleware
# that enables you to use request.ctx.session
Session(app, expires=86400)


@app.route('/')
async def index(request, **server):
    session = request.ctx.session

    if session is None:
        return b'The session will be created after you reload this page.'

    if 'visits' in session:
        session['visits'] += 1
    else:
        session['visits'] = 0

    return b'You have visited this page %d times today.' % session['visits']


if __name__ == '__main__':
    app.run('0.0.0.0', 8000, debug=True, reload=True)
