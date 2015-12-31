"""Tests for aiohttp/protocol.py"""

import unittest

from multipart_reader import errors
from multipart_reader import protocol


class TestParseHeaders(unittest.TestCase):

    def setUp(self):
        self.parser = protocol.HttpParser(8190, 32768, 8190)

    def test_parse_headers(self):
        hdrs = ('', 'test: line', ' continue',
                'test2: data', '', '')

        headers, close, compression = self.parser.parse_headers(hdrs)

        self.assertEqual(list(headers.items()),
                         [('TEST', 'line\r\n continue'), ('TEST2', 'data')])
        self.assertIsNone(close)
        self.assertIsNone(compression)

    def test_parse_headers_multi(self):
        hdrs = ('',
                'Set-Cookie: c1=cookie1',
                'Set-Cookie: c2=cookie2', '')

        headers, close, compression = self.parser.parse_headers(hdrs)

        self.assertEqual(list(headers.items()),
                         [('SET-COOKIE', 'c1=cookie1'),
                          ('SET-COOKIE', 'c2=cookie2')])
        self.assertIsNone(close)
        self.assertIsNone(compression)

    def test_conn_close(self):
        headers, close, compression = self.parser.parse_headers(
            ['', 'connection: close', ''])
        self.assertTrue(close)

    def test_conn_keep_alive(self):
        headers, close, compression = self.parser.parse_headers(
            ['', 'connection: keep-alive', ''])
        self.assertFalse(close)

    def test_conn_other(self):
        headers, close, compression = self.parser.parse_headers(
            ['', 'connection: test', '', ''])
        self.assertIsNone(close)

    def test_compression_gzip(self):
        headers, close, compression = self.parser.parse_headers(
            ['', 'content-encoding: gzip', '', ''])
        self.assertEqual('gzip', compression)

    def test_compression_deflate(self):
        headers, close, compression = self.parser.parse_headers(
            ['', 'content-encoding: deflate', '', ''])
        self.assertEqual('deflate', compression)

    def test_compression_unknown(self):
        headers, close, compression = self.parser.parse_headers(
            ['', 'content-encoding: compress', '', ''])
        self.assertIsNone(compression)

    def test_max_field_size(self):
        with self.assertRaises(errors.LineTooLong) as cm:
            parser = protocol.HttpParser(8190, 32768, 5)
            parser.parse_headers(
                ['', 'test: line data data\r\n', 'data\r\n', '\r\n'])
        self.assertIn("limit request headers fields size", str(cm.exception))

    def test_max_continuation_headers_size(self):
        with self.assertRaises(errors.LineTooLong) as cm:
            parser = protocol.HttpParser(8190, 32768, 5)
            parser.parse_headers(['', 'test: line\r\n', ' test\r\n', '\r\n'])
        self.assertIn("limit request headers fields size", str(cm.exception))

    def test_invalid_header(self):
        with self.assertRaisesRegexp(
                errors.InvalidHeader,
                "(400, message='Invalid HTTP Header: test line)"):
            self.parser.parse_headers(['', 'test line\r\n', '\r\n'])

    def test_invalid_name(self):
        with self.assertRaisesRegexp(
                errors.InvalidHeader,
                "(400, message='Invalid HTTP Header: TEST..)"):
            self.parser.parse_headers(['', 'test[]: line\r\n', '\r\n'])
