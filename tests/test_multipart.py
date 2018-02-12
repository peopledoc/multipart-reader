# -*- coding: utf-8 -*-
import io

try:
    import unittest2
except ImportError:
    import unittest as unittest2

from multipart_reader import multipart
from multipart_reader.hdrs import (
    CONTENT_DISPOSITION,
    CONTENT_ENCODING,
    CONTENT_TRANSFER_ENCODING,
    CONTENT_TYPE
)


class TestCase(unittest2.TestCase):
    pass


class Response(object):

    def __init__(self, headers, content):
        self.headers = headers
        self.content = content


class Stream(object):

    def __init__(self, content):
        self.content = io.BytesIO(content)

    def read(self, size=None):
        return self.content.read(size)

    def readline(self):
        return self.content.readline()


class StreamWithShortenRead(Stream):

    def __init__(self, content):
        self._first = True
        super(StreamWithShortenRead, self).__init__(content)

    def read(self, size=None):
        if size is not None and self._first:
            self._first = False
            size = size // 2
        return super(StreamWithShortenRead, self).read(size)


class PartReaderTestCase(TestCase):

    def setUp(self):
        super(PartReaderTestCase, self).setUp()
        self.boundary = b'--:'

    def test_next(self):
        obj = multipart.BodyPartReader(
            self.boundary, {}, Stream(b'Hello, world!\r\n--:'))
        result = obj.next()
        self.assertEqual(b'Hello, world!', result)
        self.assertTrue(obj.at_eof())

    def test_next_next(self):
        obj = multipart.BodyPartReader(
            self.boundary, {}, Stream(b'Hello, world!\r\n--:'))
        result = obj.next()
        self.assertEqual(b'Hello, world!', result)
        self.assertTrue(obj.at_eof())
        with self.assertRaises(StopIteration):
            obj.next()

    def test_read(self):
        obj = multipart.BodyPartReader(
            self.boundary, {}, Stream(b'Hello, world!\r\n--:'))
        result = obj.read()
        self.assertEqual(b'Hello, world!', result)
        self.assertTrue(obj.at_eof())

    def test_read_chunk_at_eof(self):
        obj = multipart.BodyPartReader(
            self.boundary, {}, Stream(b'--:'))
        obj._at_eof = True
        result = obj.read_chunk()
        self.assertIsNone(result)

    def test_read_chunk_requires_content_length(self):
        obj = multipart.BodyPartReader(
            self.boundary, {}, Stream(b'Hello, world!\r\n--:'))
        with self.assertRaises(AssertionError):
            obj.read_chunk()

    def test_read_chunk_properly_counts_read_bytes(self):
        expected = b'.' * 10
        size = len(expected)
        obj = multipart.BodyPartReader(
            self.boundary, {'CONTENT-LENGTH': size},
            StreamWithShortenRead(expected + b'\r\n--:--'))
        result = bytearray()
        while True:
            chunk = obj.read_chunk()
            if not chunk:
                break
            result.extend(chunk)
        self.assertEqual(size, len(result))
        self.assertEqual(b'.' * size, result)
        self.assertTrue(obj.at_eof())

    def test_read_does_reads_boundary(self):
        stream = Stream(b'Hello, world!\r\n--:')
        obj = multipart.BodyPartReader(
            self.boundary, {}, stream)
        result = obj.read()
        self.assertEqual(b'Hello, world!', result)
        self.assertEqual(b'', (stream.read()))
        self.assertEqual([b'--:'], list(obj._unread))

    def test_multiread(self):
        obj = multipart.BodyPartReader(
            self.boundary, {}, Stream(b'Hello,\r\n--:\r\n\r\nworld!\r\n--:--'))
        result = obj.read()
        self.assertEqual(b'Hello,', result)
        result = obj.read()
        self.assertIsNone(result)
        self.assertTrue(obj.at_eof())

    def test_iterate(self):
        obj = multipart.BodyPartReader(
            self.boundary, {}, Stream(b'Hello,\r\n--:\r\n\r\nworld!\r\n--:--'))
        expected = [b'Hello,', b'world!']
        for part in obj:
            self.assertEqual(part, expected.pop(0))
        self.assertTrue(obj.at_eof())

    def test_read_multiline(self):
        obj = multipart.BodyPartReader(
            self.boundary, {}, Stream(b'Hello\n,\r\nworld!\r\n--:--'))
        result = obj.read()
        self.assertEqual(b'Hello\n,\r\nworld!', result)
        result = obj.read()
        self.assertIsNone(result)
        self.assertTrue(obj.at_eof())

    def test_read_respects_content_length(self):
        obj = multipart.BodyPartReader(
            self.boundary, {'CONTENT-LENGTH': 100500},
            Stream(b'.' * 100500 + b'\r\n--:--'))
        result = obj.read()
        self.assertEqual(b'.' * 100500, result)
        self.assertTrue(obj.at_eof())

    def test_read_with_content_encoding_gzip(self):
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_ENCODING: 'gzip'},
            Stream(b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03\x0b\xc9\xccMU'
                   b'(\xc9W\x08J\xcdI\xacP\x04\x00$\xfb\x9eV\x0e\x00\x00\x00'
                   b'\r\n--:--'))
        result = obj.read(decode=True)
        self.assertEqual(b'Time to Relax!', result)

    def test_read_with_content_encoding_deflate(self):
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_ENCODING: 'deflate'},
            Stream(b'\x0b\xc9\xccMU(\xc9W\x08J\xcdI\xacP\x04\x00\r\n--:--'))
        result = obj.read(decode=True)
        self.assertEqual(b'Time to Relax!', result)

    def test_read_with_content_encoding_identity(self):
        thing = (b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03\x0b\xc9\xccMU'
                 b'(\xc9W\x08J\xcdI\xacP\x04\x00$\xfb\x9eV\x0e\x00\x00\x00'
                 b'\r\n')
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_ENCODING: 'identity'},
            Stream(thing + b'--:--'))
        result = obj.read(decode=True)
        self.assertEqual(thing[:-2], result)

    def test_read_with_content_encoding_unknown(self):
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_ENCODING: 'snappy'},
            Stream(b'\x0e4Time to Relax!\r\n--:--'))
        with self.assertRaises(RuntimeError):
            obj.read(decode=True)

    def test_read_with_content_transfer_encoding_base64(self):
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_TRANSFER_ENCODING: 'base64'},
            Stream(b'VGltZSB0byBSZWxheCE=\r\n--:--'))
        result = obj.read(decode=True)
        self.assertEqual(b'Time to Relax!', result)

    def test_read_with_content_transfer_encoding_quoted_printable(self):
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_TRANSFER_ENCODING: 'quoted-printable'},
            Stream(b'=D0=9F=D1=80=D0=B8=D0=B2=D0=B5=D1=82,'
                   b' =D0=BC=D0=B8=D1=80!\r\n--:--'))
        result = obj.read(decode=True)
        self.assertEqual(b'\xd0\x9f\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82,'
                         b' \xd0\xbc\xd0\xb8\xd1\x80!', result)

    def test_read_with_content_transfer_encoding_unknown(self):
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_TRANSFER_ENCODING: 'unknown'},
            Stream(b'\x0e4Time to Relax!\r\n--:--'))
        with self.assertRaises(RuntimeError):
            obj.read(decode=True)

    def test_read_text(self):
        obj = multipart.BodyPartReader(
            self.boundary, {}, Stream(b'Hello, world!\r\n--:--'))
        result = obj.text()
        self.assertEqual('Hello, world!', result)

    def test_read_text_encoding(self):
        obj = multipart.BodyPartReader(
            self.boundary, {},
            Stream(u'Привет, Мир!\r\n--:--'.encode('cp1251')))
        result = obj.text(encoding='cp1251')
        self.assertEqual(u'Привет, Мир!', result)

    def test_read_text_guess_encoding(self):
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_TYPE: 'text/plain;charset=cp1251'},
            Stream(u'Привет, Мир!\r\n--:--'.encode('cp1251')))
        result = obj.text()
        self.assertEqual(u'Привет, Мир!', result)

    def test_read_text_compressed(self):
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_ENCODING: 'deflate',
                            CONTENT_TYPE: 'text/plain'},
            Stream(b'\x0b\xc9\xccMU(\xc9W\x08J\xcdI\xacP\x04\x00\r\n--:--'))
        result = obj.text()
        self.assertEqual('Time to Relax!', result)

    def test_read_text_while_closed(self):
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_TYPE: 'text/plain'}, Stream(b''))
        obj._at_eof = True
        result = obj.text()
        self.assertEqual('', result)

    def test_read_json(self):
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_TYPE: 'application/json'},
            Stream(b'{"test": "passed"}\r\n--:--'))
        result = obj.json()
        self.assertEqual({'test': 'passed'}, result)

    def test_read_json_encoding(self):
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_TYPE: 'application/json'},
            Stream(u'{"тест": "пассед"}\r\n--:--'.encode('cp1251')))
        result = obj.json(encoding='cp1251')
        self.assertEqual({u'тест': u'пассед'}, result)

    def test_read_json_guess_encoding(self):
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_TYPE: 'application/json; charset=cp1251'},
            Stream(u'{"тест": "пассед"}\r\n--:--'.encode('cp1251')))
        result = obj.json()
        self.assertEqual({u'тест': u'пассед'}, result)

    def test_read_json_compressed(self):
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_ENCODING: 'deflate',
                            CONTENT_TYPE: 'application/json'},
            Stream(b'\xabV*I-.Q\xb2RP*H,.NMQ\xaa\x05\x00\r\n--:--'))
        result = obj.json()
        self.assertEqual({'test': 'passed'}, result)

    def test_read_json_while_closed(self):
        stream = Stream(b'')
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_TYPE: 'application/json'}, stream)
        obj._at_eof = True
        result = obj.json()
        self.assertIsNone(result)

    def test_read_form(self):
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_TYPE: 'application/x-www-form-urlencoded'},
            Stream(b'foo=bar&foo=baz&boo=zoo\r\n--:--'))
        result = obj.form()
        self.assertEqual([('foo', 'bar'), ('foo', 'baz'), ('boo', 'zoo')],
                         result)

    def test_read_form_encoding(self):
        obj = multipart.BodyPartReader(
            self.boundary, {CONTENT_TYPE: 'application/x-www-form-urlencoded'},
            Stream('foo=bar&foo=baz&boo=zoo\r\n--:--'.encode('cp1251')))
        result = obj.form(encoding='cp1251')
        self.assertEqual([('foo', 'bar'), ('foo', 'baz'), ('boo', 'zoo')],
                         result)

    def test_read_form_guess_encoding(self):
        obj = multipart.BodyPartReader(
            self.boundary,
            {CONTENT_TYPE: 'application/x-www-form-urlencoded; charset=utf-8'},
            Stream('foo=bar&foo=baz&boo=zoo\r\n--:--'.encode('utf-8')))
        result = obj.form()
        self.assertEqual([('foo', 'bar'), ('foo', 'baz'), ('boo', 'zoo')],
                         result)

    def test_read_form_while_closed(self):
        stream = Stream(b'')
        obj = multipart.BodyPartReader(
            self.boundary,
            {CONTENT_TYPE: 'application/x-www-form-urlencoded'}, stream)
        obj._at_eof = True
        result = obj.form()
        self.assertEqual(None, result)

    def test_release(self):
        stream = Stream(b'Hello,\r\n--:\r\n\r\nworld!\r\n--:--')
        obj = multipart.BodyPartReader(
            self.boundary, {}, stream)
        obj.release()
        self.assertTrue(obj.at_eof())
        self.assertEqual(b'\r\nworld!\r\n--:--', stream.content.read())
        self.assertEqual([b'--:\r\n'], list(obj._unread))

    def test_release_respects_content_length(self):
        obj = multipart.BodyPartReader(
            self.boundary, {'CONTENT-LENGTH': 100500},
            Stream(b'.' * 100500 + b'\r\n--:--'))
        result = obj.release()
        self.assertIsNone(result)
        self.assertTrue(obj.at_eof())

    def test_release_release(self):
        stream = Stream(b'Hello,\r\n--:\r\n\r\nworld!\r\n--:--')
        obj = multipart.BodyPartReader(
            self.boundary, {}, stream)
        obj.release()
        obj.release()
        self.assertEqual(b'\r\nworld!\r\n--:--', stream.content.read())
        self.assertEqual([b'--:\r\n'], list(obj._unread))

    def test_filename(self):
        part = multipart.BodyPartReader(
            self.boundary,
            {CONTENT_DISPOSITION: 'attachment; filename=foo.html'},
            None)
        self.assertEqual('foo.html', part.filename)


class MultipartReaderTestCase(TestCase):

    def test_dispatch(self):
        reader = multipart.MultipartReader(
            {CONTENT_TYPE: 'multipart/related;boundary=":"'},
            Stream(b'--:\r\n\r\necho\r\n--:--'))
        res = reader._get_part_reader({CONTENT_TYPE: 'text/plain'})
        self.assertIsInstance(res, reader.part_reader_cls)

    def test_dispatch_bodypart(self):
        reader = multipart.MultipartReader(
            {CONTENT_TYPE: 'multipart/related;boundary=":"'},
            Stream(b'--:\r\n\r\necho\r\n--:--'))
        res = reader._get_part_reader({CONTENT_TYPE: 'text/plain'})
        self.assertIsInstance(res, reader.part_reader_cls)

    def test_dispatch_multipart(self):
        reader = multipart.MultipartReader(
            {CONTENT_TYPE: 'multipart/related;boundary=":"'},
            Stream(b'----:--\r\n'
                   b'\r\n'
                   b'test\r\n'
                   b'----:--\r\n'
                   b'\r\n'
                   b'passed\r\n'
                   b'----:----\r\n'
                   b'--:--'))
        res = reader._get_part_reader(
            {CONTENT_TYPE: 'multipart/related;boundary=--:--'})
        self.assertIsInstance(res, reader.__class__)

    def test_dispatch_custom_multipart_reader(self):
        class CustomReader(multipart.MultipartReader):
            pass
        reader = multipart.MultipartReader(
            {CONTENT_TYPE: 'multipart/related;boundary=":"'},
            Stream(b'----:--\r\n'
                   b'\r\n'
                   b'test\r\n'
                   b'----:--\r\n'
                   b'\r\n'
                   b'passed\r\n'
                   b'----:----\r\n'
                   b'--:--'))
        reader.multipart_reader_cls = CustomReader
        res = reader._get_part_reader(
            {CONTENT_TYPE: 'multipart/related;boundary=--:--'})
        self.assertIsInstance(res, CustomReader)

    def test_emit_next(self):
        reader = multipart.MultipartReader(
            {CONTENT_TYPE: 'multipart/related;boundary=":"'},
            Stream(b'--:\r\n\r\necho\r\n--:--'))
        res = reader.next()
        self.assertIsInstance(res, reader.part_reader_cls)

    def test_invalid_boundary(self):
        reader = multipart.MultipartReader(
            {CONTENT_TYPE: 'multipart/related;boundary=":"'},
            Stream(b'---:\r\n\r\necho\r\n---:--'))
        with self.assertRaises(ValueError):
            reader.next()

    def test_release(self):
        reader = multipart.MultipartReader(
            {CONTENT_TYPE: 'multipart/mixed;boundary=":"'},
            Stream(b'--:\r\n'
                   b'Content-Type: multipart/related;boundary=--:--\r\n'
                   b'\r\n'
                   b'----:--\r\n'
                   b'\r\n'
                   b'test\r\n'
                   b'----:--\r\n'
                   b'\r\n'
                   b'passed\r\n'
                   b'----:----\r\n'
                   b'--:--'))
        reader.release()
        self.assertTrue(reader.at_eof())

    def test_release_release(self):
        reader = multipart.MultipartReader(
            {CONTENT_TYPE: 'multipart/related;boundary=":"'},
            Stream(b'--:\r\n\r\necho\r\n--:--'))
        reader.release()
        self.assertTrue(reader.at_eof())
        reader.release()
        self.assertTrue(reader.at_eof())

    def test_release_next(self):
        reader = multipart.MultipartReader(
            {CONTENT_TYPE: 'multipart/related;boundary=":"'},
            Stream(b'--:\r\n\r\necho\r\n--:--'))
        reader.release()
        self.assertTrue(reader.at_eof())
        with self.assertRaises(StopIteration):
            reader.next()

    def test_second_next_releases_previous_object(self):
        reader = multipart.MultipartReader(
            {CONTENT_TYPE: 'multipart/related;boundary=":"'},
            Stream(b'--:\r\n'
                   b'\r\n'
                   b'test\r\n'
                   b'--:\r\n'
                   b'\r\n'
                   b'passed\r\n'
                   b'--:--'))
        first = reader.next()
        self.assertIsInstance(first, multipart.BodyPartReader)
        second = reader.next()
        self.assertTrue(first.at_eof())
        self.assertFalse(second.at_eof())

    def test_release_without_read_the_last_object(self):
        reader = multipart.MultipartReader(
            {CONTENT_TYPE: 'multipart/related;boundary=":"'},
            Stream(b'--:\r\n'
                   b'\r\n'
                   b'test\r\n'
                   b'--:\r\n'
                   b'\r\n'
                   b'passed\r\n'
                   b'--:--'))
        first = reader.next()
        second = reader.next()

        with self.assertRaises(StopIteration):
            reader.next()

        self.assertTrue(first.at_eof())
        self.assertTrue(second.at_eof())

    def test_read_chunk_doesnt_breaks_reader(self):
        reader = multipart.MultipartReader(
            {CONTENT_TYPE: 'multipart/related;boundary=":"'},
            Stream(b'--:\r\n'
                   b'Content-Length: 4\r\n\r\n'
                   b'test'
                   b'\r\n--:\r\n'
                   b'Content-Length: 6\r\n\r\n'
                   b'passed'
                   b'\r\n--:--'))
        for part in reader:
            while not part.at_eof():
                part.read_chunk(3)


class ParseContentDispositionTestCase(unittest2.TestCase):
    # http://greenbytes.de/tech/tc2231/

    def test_parse_empty(self):
        disptype, params = multipart.parse_content_disposition(None)
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_inlonly(self):
        disptype, params = multipart.parse_content_disposition('inline')
        self.assertEqual('inline', disptype)
        self.assertEqual({}, params)

    def test_inlonlyquoted(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition('"inline"')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_inlwithasciifilename(self):
        disptype, params = multipart.parse_content_disposition(
            'inline; filename="foo.html"')
        self.assertEqual('inline', disptype)
        self.assertEqual({'filename': 'foo.html'}, params)

    def test_inlwithfnattach(self):
        disptype, params = multipart.parse_content_disposition(
            'inline; filename="Not an attachment!"')
        self.assertEqual('inline', disptype)
        self.assertEqual({'filename': 'Not an attachment!'}, params)

    def test_attonly(self):
        disptype, params = multipart.parse_content_disposition('attachment')
        self.assertEqual('attachment', disptype)
        self.assertEqual({}, params)

    def test_attonlyquoted(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                '"attachment"')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attonlyucase(self):
        disptype, params = multipart.parse_content_disposition('ATTACHMENT')
        self.assertEqual('attachment', disptype)
        self.assertEqual({}, params)

    def test_attwithasciifilename(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="foo.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo.html'}, params)

    def test_inlwithasciifilenamepdf(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="foo.pdf"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo.pdf'}, params)

    def test_attwithasciifilename25(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="0000000000111111111122222"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': '0000000000111111111122222'}, params)

    def test_attwithasciifilename35(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="00000000001111111111222222222233333"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': '00000000001111111111222222222233333'},
                         params)

    def test_attwithasciifnescapedchar(self):
        disptype, params = multipart.parse_content_disposition(
            r'attachment; filename="f\oo.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo.html'}, params)

    def test_attwithasciifnescapedquote(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="\"quoting\" tested.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': '"quoting" tested.html'}, params)

    @unittest2.skip('need more smart parser which respects quoted text')
    def test_attwithquotedsemicolon(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="Here\'s a semicolon;.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'Here\'s a semicolon;.html'}, params)

    def test_attwithfilenameandextparam(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; foo="bar"; filename="foo.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo.html', 'foo': 'bar'}, params)

    def test_attwithfilenameandextparamescaped(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; foo="\"\\";filename="foo.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo.html', 'foo': '"\\'}, params)

    def test_attwithasciifilenameucase(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; FILENAME="foo.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo.html'}, params)

    def test_attwithasciifilenamenq(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename=foo.html')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo.html'}, params)

    def test_attwithtokfncommanq(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment; filename=foo,bar.html')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attwithasciifilenamenqs(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment; filename=foo.html ;')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attemptyparam(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment; ;filename=foo')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attwithasciifilenamenqws(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment; filename=foo bar.html')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attwithfntokensq(self):
        disptype, params = multipart.parse_content_disposition(
            "attachment; filename='foo.html'")
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': "'foo.html'"}, params)

    def test_attwithisofnplain(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="foo-ä.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo-ä.html'}, params)

    def test_attwithutf8fnplain(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="foo-Ã¤.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo-Ã¤.html'}, params)

    def test_attwithfnrawpctenca(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="foo-%41.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo-%41.html'}, params)

    def test_attwithfnusingpct(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="50%.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': '50%.html'}, params)

    def test_attwithfnrawpctencaq(self):
        disptype, params = multipart.parse_content_disposition(
            r'attachment; filename="foo-%\41.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': r'foo-%41.html'}, params)

    def test_attwithnamepct(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="foo-%41.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo-%41.html'}, params)

    def test_attwithfilenamepctandiso(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="ä-%41.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'ä-%41.html'}, params)

    def test_attwithfnrawpctenclong(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="foo-%c3%a4-%e2%82%ac.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo-%c3%a4-%e2%82%ac.html'}, params)

    def test_attwithasciifilenamews1(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename ="foo.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo.html'}, params)

    def test_attwith2filenames(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment; filename="foo.html"; filename="bar.html"')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attfnbrokentoken(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment; filename=foo[1](2).html')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attfnbrokentokeniso(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment; filename=foo-ä.html')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attfnbrokentokenutf(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment; filename=foo-Ã¤.html')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attmissingdisposition(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'filename=foo.html')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attmissingdisposition2(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'x=y; filename=foo.html')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attmissingdisposition3(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                '"foo; filename=bar;baz"; filename=qux')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attmissingdisposition4(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'filename=foo.html, filename=bar.html')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_emptydisposition(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                '; filename=foo.html')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_doublecolon(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                ': inline; attachment; filename=foo.html')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attandinline(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'inline; attachment; filename=foo.html')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attandinline2(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment; inline; filename=foo.html')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attbrokenquotedfn(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment; filename="foo.html".txt')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attbrokenquotedfn2(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment; filename="bar')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attbrokenquotedfn3(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment; filename=foo"bar;baz"qux')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attmultinstances(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment; filename=foo.html, attachment; filename=bar.html')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attmissingdelim(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment; foo=foo filename=bar')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attmissingdelim2(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment; filename=bar foo=foo')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attmissingdelim3(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment filename=bar')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attreversed(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'filename=foo.html; attachment')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attconfusedparam(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; xfilename=foo.html')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'xfilename': 'foo.html'}, params)

    def test_attabspath(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="/foo.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo.html'}, params)

    def test_attabspathwin(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="\\foo.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo.html'}, params)

    def test_attcdate(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; creation-date="Wed, 12 Feb 1997 16:29:51 -0500"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'creation-date': 'Wed, 12 Feb 1997 16:29:51 -0500'},
                         params)

    def test_attmdate(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; modification-date="Wed, 12 Feb 1997 16:29:51 -0500"')
        self.assertEqual('attachment', disptype)
        self.assertEqual(
            {'modification-date': 'Wed, 12 Feb 1997 16:29:51 -0500'},
            params)

    def test_dispext(self):
        disptype, params = multipart.parse_content_disposition('foobar')
        self.assertEqual('foobar', disptype)
        self.assertEqual({}, params)

    def test_dispextbadfn(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; example="filename=example.txt"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'example': 'filename=example.txt'}, params)

    def test_attwithisofn2231iso(self):
        disptype, params = multipart.parse_content_disposition(
            "attachment; filename*=iso-8859-1''foo-%E4.html")
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename*': u'foo-ä.html'}, params)

    def test_attwithfn2231utf8(self):
        disptype, params = multipart.parse_content_disposition(
            "attachment; filename*=UTF-8''foo-%c3%a4-%e2%82%ac.html")
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename*': u'foo-ä-€.html'}, params)

    def test_attwithfn2231noc(self):
        disptype, params = multipart.parse_content_disposition(
            "attachment; filename*=''foo-%c3%a4-%e2%82%ac.html")
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename*': u'foo-ä-€.html'}, params)

    def test_attwithfn2231utf8comp(self):
        disptype, params = multipart.parse_content_disposition(
            "attachment; filename*=UTF-8''foo-a%cc%88.html")
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename*': u'foo-ä.html'}, params)

    @unittest2.skip('should raise decoding error: %82 is invalid for latin1')
    def test_attwithfn2231utf8_bad(self):
        with self.assertWarns(multipart.BadContentDispositionParam):
            disptype, params = multipart.parse_content_disposition(
                "attachment; filename*=iso-8859-1''foo-%c3%a4-%e2%82%ac.html")
        self.assertEqual('attachment', disptype)
        self.assertEqual({}, params)

    @unittest2.skip('should raise decoding error: %E4 is invalid for utf-8')
    def test_attwithfn2231iso_bad(self):
        with self.assertWarns(multipart.BadContentDispositionParam):
            disptype, params = multipart.parse_content_disposition(
                "attachment; filename*=utf-8''foo-%E4.html")
        self.assertEqual('attachment', disptype)
        self.assertEqual({}, params)

    def test_attwithfn2231ws1(self):
        with self.assertWarns(multipart.BadContentDispositionParam):
            disptype, params = multipart.parse_content_disposition(
                "attachment; filename *=UTF-8''foo-%c3%a4.html")
        self.assertEqual('attachment', disptype)
        self.assertEqual({}, params)

    def test_attwithfn2231ws2(self):
        disptype, params = multipart.parse_content_disposition(
            "attachment; filename*= UTF-8''foo-%c3%a4.html")
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename*': u'foo-ä.html'}, params)

    def test_attwithfn2231ws3(self):
        disptype, params = multipart.parse_content_disposition(
            "attachment; filename* =UTF-8''foo-%c3%a4.html")
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename*': u'foo-ä.html'}, params)

    def test_attwithfn2231quot(self):
        with self.assertWarns(multipart.BadContentDispositionParam):
            disptype, params = multipart.parse_content_disposition(
                "attachment; filename*=\"UTF-8''foo-%c3%a4.html\"")
        self.assertEqual('attachment', disptype)
        self.assertEqual({}, params)

    def test_attwithfn2231quot2(self):
        with self.assertWarns(multipart.BadContentDispositionParam):
            disptype, params = multipart.parse_content_disposition(
                "attachment; filename*=\"foo%20bar.html\"")
        self.assertEqual('attachment', disptype)
        self.assertEqual({}, params)

    def test_attwithfn2231singleqmissing(self):
        with self.assertWarns(multipart.BadContentDispositionParam):
            disptype, params = multipart.parse_content_disposition(
                "attachment; filename*=UTF-8'foo-%c3%a4.html")
        self.assertEqual('attachment', disptype)
        self.assertEqual({}, params)

    @unittest2.skip('urllib.parse.unquote is tolerate to standalone % chars')
    def test_attwithfn2231nbadpct1(self):
        with self.assertWarns(multipart.BadContentDispositionParam):
            disptype, params = multipart.parse_content_disposition(
                "attachment; filename*=UTF-8''foo%")
        self.assertEqual('attachment', disptype)
        self.assertEqual({}, params)

    @unittest2.skip('urllib.parse.unquote is tolerate to standalone % chars')
    def test_attwithfn2231nbadpct2(self):
        with self.assertWarns(multipart.BadContentDispositionParam):
            disptype, params = multipart.parse_content_disposition(
                "attachment; filename*=UTF-8''f%oo.html")
        self.assertEqual('attachment', disptype)
        self.assertEqual({}, params)

    def test_attwithfn2231dpct(self):
        disptype, params = multipart.parse_content_disposition(
            "attachment; filename*=UTF-8''A-%2541.html")
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename*': 'A-%41.html'}, params)

    def test_attwithfn2231abspathdisguised(self):
        disptype, params = multipart.parse_content_disposition(
            "attachment; filename*=UTF-8''%5cfoo.html")
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename*': '\\foo.html'}, params)

    def test_attfncont(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename*0="foo."; filename*1="html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename*0': 'foo.',
                          'filename*1': 'html'}, params)

    def test_attfncontqs(self):
        disptype, params = multipart.parse_content_disposition(
            r'attachment; filename*0="foo"; filename*1="\b\a\r.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename*0': 'foo',
                          'filename*1': 'bar.html'}, params)

    def test_attfncontenc(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename*0*=UTF-8''foo-%c3%a4; filename*1=".html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename*0*': 'UTF-8''foo-%c3%a4',
                          'filename*1': '.html'}, params)

    def test_attfncontlz(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename*0="foo"; filename*01="bar"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename*0': 'foo',
                          'filename*01': 'bar'}, params)

    def test_attfncontnc(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename*0="foo"; filename*2="bar"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename*0': 'foo',
                          'filename*2': 'bar'}, params)

    def test_attfnconts1(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename*0="foo."; filename*2="html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename*0': 'foo.',
                          'filename*2': 'html'}, params)

    def test_attfncontord(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename*1="bar"; filename*0="foo"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename*0': 'foo',
                          'filename*1': 'bar'}, params)

    def test_attfnboth(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="foo-ae.html";'
            " filename*=UTF-8''foo-%c3%a4.html")
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo-ae.html',
                          'filename*': u'foo-ä.html'}, params)

    def test_attfnboth2(self):
        disptype, params = multipart.parse_content_disposition(
            "attachment; filename*=UTF-8''foo-%c3%a4.html;"
            ' filename="foo-ae.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': 'foo-ae.html',
                          'filename*': u'foo-ä.html'}, params)

    def test_attfnboth3(self):
        disptype, params = multipart.parse_content_disposition(
            "attachment; filename*0*=ISO-8859-15''euro-sign%3d%a4;"
            " filename*=ISO-8859-1''currency-sign%3d%a4")
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename*': u'currency-sign=¤',
                          'filename*0*': "ISO-8859-15''euro-sign%3d%a4"},
                         params)

    def test_attnewandfn(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; foobar=x; filename="foo.html"')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'foobar': 'x',
                          'filename': 'foo.html'}, params)

    def test_attrfc2047token(self):
        with self.assertWarns(multipart.BadContentDispositionHeader):
            disptype, params = multipart.parse_content_disposition(
                'attachment; filename==?ISO-8859-1?Q?foo-=E4.html?=')
        self.assertEqual(None, disptype)
        self.assertEqual({}, params)

    def test_attrfc2047quoted(self):
        disptype, params = multipart.parse_content_disposition(
            'attachment; filename="=?ISO-8859-1?Q?foo-=E4.html?="')
        self.assertEqual('attachment', disptype)
        self.assertEqual({'filename': '=?ISO-8859-1?Q?foo-=E4.html?='}, params)

    def test_bad_continuous_param(self):
        with self.assertWarns(multipart.BadContentDispositionParam):
            disptype, params = multipart.parse_content_disposition(
                'attachment; filename*0=foo bar')
        self.assertEqual('attachment', disptype)
        self.assertEqual({}, params)


class ContentDispositionFilenameTestCase(unittest2.TestCase):
    # http://greenbytes.de/tech/tc2231/

    def test_no_filename(self):
        self.assertIsNone(multipart.content_disposition_filename({}))
        self.assertIsNone(
            multipart.content_disposition_filename({'foo': 'bar'}))

    def test_filename(self):
        params = {'filename': 'foo.html'}
        self.assertEqual('foo.html',
                         multipart.content_disposition_filename(params))

    def test_filename_ext(self):
        params = {'filename*': 'файл.html'}
        self.assertEqual('файл.html',
                         multipart.content_disposition_filename(params))

    def test_attfncont(self):
        params = {'filename*0': 'foo.', 'filename*1': 'html'}
        self.assertEqual('foo.html',
                         multipart.content_disposition_filename(params))

    def test_attfncontqs(self):
        params = {'filename*0': 'foo', 'filename*1': 'bar.html'}
        self.assertEqual('foobar.html',
                         multipart.content_disposition_filename(params))

    def test_attfncontenc(self):
        params = {'filename*0*': "UTF-8''foo-%c3%a4",
                  'filename*1': '.html'}
        self.assertEqual(u'foo-ä.html',
                         multipart.content_disposition_filename(params))

    def test_attfncontlz(self):
        params = {'filename*0': 'foo',
                  'filename*01': 'bar'}
        self.assertEqual('foo',
                         multipart.content_disposition_filename(params))

    def test_attfncontnc(self):
        params = {'filename*0': 'foo',
                  'filename*2': 'bar'}
        self.assertEqual('foo',
                         multipart.content_disposition_filename(params))

    def test_attfnconts1(self):
        params = {'filename*1': 'foo',
                  'filename*2': 'bar'}
        self.assertEqual(None,
                         multipart.content_disposition_filename(params))

    def test_attfnboth(self):
        params = {'filename': 'foo-ae.html',
                  'filename*': 'foo-ä.html'}
        self.assertEqual('foo-ä.html',
                         multipart.content_disposition_filename(params))

    def test_attfnboth3(self):
        params = {'filename*0*': "ISO-8859-15''euro-sign%3d%a4",
                  'filename*': 'currency-sign=¤'}
        self.assertEqual('currency-sign=¤',
                         multipart.content_disposition_filename(params))

    def test_attrfc2047quoted(self):
        params = {'filename': '=?ISO-8859-1?Q?foo-=E4.html?='}
        self.assertEqual('=?ISO-8859-1?Q?foo-=E4.html?=',
                         multipart.content_disposition_filename(params))
