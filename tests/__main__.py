#!/usr/bin/env python3

import multiprocessing as mp
import os
import sys
import signal
import unittest

# makes imports relative from the repo directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.http_server import app, HTTP_HOST, HTTP_PORT  # noqa: E402


def main():
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
            os.kill(p.pid, signal.SIGTERM)
            p.join()


if __name__ == '__main__':
    main()
