#!/usr/bin/env python3

import multiprocessing as mp
import os
import signal
import sys
import time
import unittest

# makes imports relative from the repo directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.http_server import (  # noqa: E402
    app,
    HTTP_HOST,
    HTTP_PORT
)
from tests.utils import getcontents  # noqa: E402

_EXPIRES = time.time() + 1800


class TestHTTPServer(unittest.TestCase):
    def setUp(self):
        print('\r\n[', self.id(), ']')

    def test_get_nosetcookie(self):
        header, body = getcontents(host=HTTP_HOST,
                                   port=HTTP_PORT,
                                   method='GET',
                                   url='/',
                                   version='1.0')

        self.assertEqual(
            header[:header.find(b'\r\n')], b'HTTP/1.0 503 Service Unavailable'
        )
        self.assertFalse(b'\r\nCache-Control: no-cache,' in header)
        self.assertFalse(b'\r\nSet-Cookie: sess=' in header)

    def test_get_header(self):
        header, body = getcontents(host=HTTP_HOST,
                                   port=HTTP_PORT,
                                   method='GET',
                                   url='/cookies',
                                   version='1.0')

        self.assertEqual(header[:header.find(b'\r\n')], b'HTTP/1.0 200 OK')
        self.assertTrue(b'\r\nCache-Control: no-cache,' in body)
        self.assertTrue(b'\r\nSet-Cookie: sess=' in body)

    def test_get_ok(self):
        header, body = getcontents(
            host=HTTP_HOST,
            port=HTTP_PORT,
            raw=b'GET /cookies HTTP/1.0\r\nHost: localhost\r\n'
                b'Cookie: sess=5e55.' + (b'%d' % _EXPIRES) +
                b'\r\n\r\n'
        )

        self.assertEqual(header[:header.find(b'\r\n')], b'HTTP/1.0 200 OK')
        self.assertEqual(b'OK', body)

    def test_get_ok_badfile(self):
        header, body = getcontents(
            host=HTTP_HOST,
            port=HTTP_PORT,
            raw=b'GET /cookies HTTP/1.0\r\nHost: localhost\r\nCookie: '
                b'sess=5e55bad.' + (b'%d' % _EXPIRES) +
                b'\r\n\r\n'
        )

        self.assertEqual(header[:header.find(b'\r\n')], b'HTTP/1.0 200 OK')
        self.assertEqual(b'OK', body)

    def test_get_ok_expiredsess(self):
        header, body = getcontents(
            host=HTTP_HOST,
            port=HTTP_PORT,
            raw=b'GET /cookies HTTP/1.0\r\nHost: localhost\r\n'
                b'Cookie: sess=a.0\r\n\r\n'
        )

        self.assertEqual(header[:header.find(b'\r\n')], b'HTTP/1.0 200 OK')
        self.assertEqual(b'OK', body)

    def test_get_notfound(self):
        header, body = getcontents(host=HTTP_HOST,
                                   port=HTTP_PORT,
                                   method='GET',
                                   url='/invalid',
                                   version='1.1')

        self.assertEqual(
            header[:header.find(b'\r\n')], b'HTTP/1.1 404 Not Found'
        )
        # cookies may also be present on the 404 page
        self.assertTrue(b'\r\nSet-Cookie: sess=' in header)

    def test_get_badcookie_keyerror(self):
        header, body = getcontents(
            host=HTTP_HOST,
            port=HTTP_PORT,
            raw=b'GET /cookies HTTP/1.1\r\nHost: localhost\r\n'
                b'Cookie: sess=xx\r\n\r\n'
        )

        self.assertEqual(
            header[:header.find(b'\r\n')], b'HTTP/1.1 403 Forbidden'
        )
        self.assertEqual(b'bad cookie', body)

    def test_get_badcookie_valueerror(self):
        header, body = getcontents(
            host=HTTP_HOST,
            port=HTTP_PORT,
            raw=b'GET /cookies HTTP/1.1\r\nHost: localhost\r\n'
                b'Cookie: sess=x.0\r\n\r\n'
        )

        self.assertEqual(
            header[:header.find(b'\r\n')], b'HTTP/1.1 403 Forbidden'
        )
        self.assertEqual(b'bad cookie', body)


if __name__ == '__main__':
    mp.set_start_method('spawn')

    p = mp.Process(
        target=app.run,
        kwargs=dict(host=HTTP_HOST, port=HTTP_PORT, debug=False)
    )
    p.start()

    try:
        unittest.main()
    finally:
        if p.is_alive():
            os.kill(p.pid, signal.SIGTERM)
            p.join()
