# tremolo-session
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=nggit_tremolo-session&metric=coverage)](https://sonarcloud.io/summary/new_code?id=nggit_tremolo-session)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=nggit_tremolo-session&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=nggit_tremolo-session)

A simple, file-based session middleware for [Tremolo](https://github.com/nggit/tremolo).

See also: [tremolo-login](https://github.com/nggit/tremolo-login).

## Usage
```python
#!/usr/bin/env python3

from tremolo import Application
from tremolo_session import Session

app = Application()

# this is a session middleware
# that enables you to use context.session or request.ctx.session
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
```

## Installing
```
python3 -m pip install --upgrade tremolo_session
```

## Testing
Just run `python3 -m tests`.

Or if you also want measurements with [coverage](https://coverage.readthedocs.io/):

```
coverage run -m tests
coverage combine
coverage report
coverage html # to generate html reports
```

## License
MIT License
