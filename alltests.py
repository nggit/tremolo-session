#!/usr/bin/env python3

import multiprocessing as mp
import os
import signal
import unittest

from tests.http_server import app, HTTP_HOST, HTTP_PORT

if __name__ == '__main__':
    mp.set_start_method('spawn')

    p = mp.Process(
        target=app.run,
        kwargs=dict(host=HTTP_HOST, port=HTTP_PORT, debug=False)
    )
    p.start()

    try:
        suite = unittest.TestLoader().discover('tests')
        unittest.TextTestRunner().run(suite)
    finally:
        if p.is_alive():
            os.kill(p.pid, signal.SIGINT)
            p.join()
