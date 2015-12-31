import json
import unittest
import io

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase

from multipart_reader import MultipartReader


TXT = u"""
Python will save the world.
I don't know how.
But it will.
""".strip()


class MultipartReaderTestCase(unittest.TestCase):

    def _to_stream(self, content):
        stream = io.BytesIO()
        stream.write(content)
        stream.seek(0)
        return stream

    def _get_multipart(self, subtype):

        multipart = MIMEMultipart(subtype)

        part = MIMEBase('application', 'json')
        part.set_payload(json.dumps({'foo': 'bar'}))
        multipart.attach(part)

        part = MIMEBase('application', 'octet-stream')
        part.set_payload(TXT)
        part.add_header('Content-Disposition', 'attachment',
                        filename='python-save-the-world.txt')
        multipart.attach(part)

        return multipart

    def _get_reader(self, subtype):
        multipart = self._get_multipart(subtype)
        content = multipart.as_string().split('\n\n', 1)[1]
        headers = dict(multipart.items())
        return MultipartReader(headers, self._to_stream(content))

    def _test_reader(self, subtype):

        reader = self._get_reader(subtype)

        json_part = reader.next()
        self.assertEqual(json_part.json(), {'foo': 'bar'})

        file_part = reader.next()
        self.assertEqual(file_part.text(), TXT)
        self.assertEqual(file_part.filename, 'python-save-the-world.txt')

    def test_multipart_reader_form_data(self):
        self._test_reader('form-data')

    def test_multipart_reader_related(self):
        self._test_reader('related')

    def test_multipart_reader_mixed(self):
        self._test_reader('mixed')
