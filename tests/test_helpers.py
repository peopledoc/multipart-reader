import unittest

from multipart_reader import helpers


class TestHelpers(unittest.TestCase):

    def test_parse_mimetype_1(self):
        self.assertEqual(helpers.parse_mimetype(''), ('', '', '', {}))

    def test_parse_mimetype_2(self):
        self.assertEqual(helpers.parse_mimetype('*'), ('*', '*', '', {}))

    def test_parse_mimetype_3(self):
        self.assertEqual(helpers.parse_mimetype('application/json'),
                         ('application', 'json', '', {}))

    def test_parse_mimetype_4(self):
        self.assertEqual(
            helpers.parse_mimetype('application/json;  charset=utf-8'),
            ('application', 'json', '', {'charset': 'utf-8'}))

    def test_parse_mimetype_5(self):
        self.assertEqual(
            helpers.parse_mimetype('''application/json; charset=utf-8;'''),
            ('application', 'json', '', {'charset': 'utf-8'}))

    def test_parse_mimetype_6(self):
        self.assertEqual(
            helpers.parse_mimetype('ApPlIcAtIoN/JSON;ChaRseT="UTF-8"'),
            ('application', 'json', '', {'charset': 'UTF-8'}))

    def test_parse_mimetype_7(self):
        self.assertEqual(helpers.parse_mimetype('application/rss+xml'),
                         ('application', 'rss', 'xml', {}))

    def test_parse_mimetype_8(self):
        self.assertEqual(helpers.parse_mimetype('text/plain;base64'),
                         ('text', 'plain', '', {'base64': ''}))
