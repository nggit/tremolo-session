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
from tests.netizen import HTTPClient  # noqa: E402

_EXPIRES = time.time() + 1800


class TestHTTP(unittest.TestCase):
    def setUp(self):
        print('\r\n[', self.id(), ']')

        self.client = HTTPClient(HTTP_HOST, HTTP_PORT, timeout=10, retries=10)

    def test_get_nosetcookie(self):
        with self.client:
            response = self.client.send(b'GET / HTTP/1.0')

            self.assertEqual(response.status, 503)
            self.assertEqual(response.message, b'Service Unavailable')
            self.assertFalse(b'cache-control' in response.headers)
            self.assertFalse(b'set-cookie' in response.headers)

    def test_get_header(self):
        with self.client:
            response = self.client.send(b'GET /cookies HTTP/1.0')
            body = response.body()

            self.assertEqual(response.status, 200)
            self.assertEqual(response.message, b'OK')
            self.assertTrue(b'\r\nCache-Control: no-cache,' in body)
            self.assertTrue(b'\r\nSet-Cookie: sess=' in body)

    def test_get_ok(self):
        with self.client:
            response = self.client.send(
                b'GET /cookies HTTP/1.0',
                b'Cookie: sess=5e55.%d' % _EXPIRES
            )

            self.assertEqual(response.status, 200)
            self.assertEqual(response.message, b'OK')
            self.assertEqual(response.body(), b'OK')

    def test_get_ok_badfile(self):
        with self.client:
            response = self.client.send(
                b'GET /cookies HTTP/1.0',
                b'Cookie: sess=5e55badf.%d' % _EXPIRES
            )

            self.assertEqual(response.status, 200)
            self.assertEqual(response.message, b'OK')
            self.assertEqual(response.body(), b'OK')

    def test_get_ok_expiredsess(self):
        with self.client:
            response = self.client.send(
                b'GET /cookies HTTP/1.0',
                b'Cookie: sess=ab.0'
            )

            self.assertEqual(response.status, 200)
            self.assertEqual(response.message, b'OK')
            self.assertEqual(response.body(), b'OK')

    def test_get_notfound(self):
        with self.client:
            response = self.client.send(b'GET /invalid HTTP/1.1')

            self.assertEqual(response.status, 404)
            self.assertEqual(response.message, b'Not Found')
            self.assertFalse(b'set-cookie' in response.headers)

    def test_get_badcookie_valueerror(self):
        with self.client:
            response = self.client.send(
                b'GET /cookies HTTP/1.1',
                b'Cookie: sess=xx.0'
            )

            self.assertEqual(response.status, 403)
            self.assertEqual(response.message, b'Forbidden')
            self.assertEqual(response.body(), b'bad cookie')

    def test_get_badcookie_valueerror_unpack(self):
        with self.client:
            response = self.client.send(
                b'GET /cookies HTTP/1.1',
                b'Cookie: sess=xx'
            )

            self.assertEqual(response.status, 403)
            self.assertEqual(response.message, b'Forbidden')
            self.assertEqual(response.body(), b'bad cookie')


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
