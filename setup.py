#!/usr/bin/env python
import os

from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))


setup(
    name='multipart-reader',
    version=open(os.path.join(here, 'VERSION')).read().strip(),
    description='Multipart/* reader extracted from awsome `aiohttp` project, cf.: http://aiohttp.readthedocs.org/en/stable/multipart.html.',  # noqa
    long_description=open(os.path.join(here, 'README.rst')).read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
    ],
    keywords=[
        'multipart',
    ],
    author='Florent Pigout',
    author_email='florent.pigout@people-doc.com',
    url='https://github.com/novafloss/multipart-reader',
    license='MIT',
    install_requires=[
        'future',
        'setuptools>=17.1',
    ],
    extras_require={
        'test': [
            'flake8',
            'unittest2'
        ],
        'release': [
            'wheel',
            'zest.releaser'
        ],
    },
    packages=[
        'multipart_reader'
    ],
)
