__all__ = ('getcontents',)

import socket  # noqa: E402
import time  # noqa: E402


# a simple HTTP client for tests
def getcontents(
        host='localhost',
        port=80,
        method='GET',
        url='/',
        version='1.1',
        headers=[],
        data='',
        raw=b''
        ):
    if raw == b'':
        content_length = len(data)

        if content_length > 0:
            if headers == []:
                headers.append(
                    'Content-Type: application/x-www-form-urlencoded'
                )

            headers.append('Content-Length: {:d}'.format(content_length))

        raw = ('{:s} {:s} HTTP/{:s}\r\nHost: {:s}:{:d}\r\n{:s}\r\n\r\n'
               '{:s}').format(method,
                              url,
                              version,
                              host,
                              port,
                              '\r\n'.join(headers),
                              data).encode('latin-1')

    family = socket.AF_INET

    if ':' in host:
        family = socket.AF_INET6

    if host in ('0.0.0.0', '::'):
        host = 'localhost'

    with socket.socket(family, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.settimeout(10)

        while sock.connect_ex((host, port)) != 0:
            time.sleep(1)

        payload = b''

        if b'\r\nupgrade:' in raw.lower():
            payload = raw[raw.find(b'\r\n\r\n') + 4:]
            raw = raw[:raw.find(b'\r\n\r\n') + 4]

        sock.sendall(raw)

        response_data = bytearray()
        response_header = b''
        buf = True

        while buf:
            buf = sock.recv(4096)
            response_data.extend(buf)

            header_size = response_data.find(b'\r\n\r\n')
            response_header = response_data[:header_size]

            if header_size > -1:
                _response_header = response_header.lower()

                if _response_header.startswith(
                        'http/{:s} 100 continue'
                        .format(version).encode('latin-1')):
                    del response_data[:]
                    continue

                if _response_header.startswith(
                        'http/{:s} 101 '
                        .format(version).encode('latin-1')):
                    del response_data[:]
                    sock.sendall(payload)
                    continue

                if method.upper() == 'HEAD':
                    break

                if (
                        b'\r\ntransfer-encoding: chunked' in
                        _response_header and
                        response_data.endswith(b'\r\n0\r\n\r\n')
                        ):
                    break

                if (
                        (b'\r\ncontent-length: %d\r\n' %
                            (len(response_data) - header_size - 4)) in
                        _response_header
                        ):
                    break

            if payload != b'':
                return response_data

        return response_header, response_data[header_size + 4:]
