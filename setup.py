#!/usr/bin/env python3

from setuptools import setup

if __name__ == '__main__':
    import sys

    if len(sys.argv) == 1:
        sys.argv.append('install')

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='tremolo-session',
    version='1.0.2',
    license='MIT',
    author='nggit',
    author_email='contact@anggit.com',
    description=('A simple, file-based session middleware for Tremolo.'),
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/nggit/tremolo-session',
    packages=['tremolo_session'],
    install_requires=['tremolo'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
)
