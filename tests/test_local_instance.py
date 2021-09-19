"""
This unittest tests the parsing of locally saved instance documents.
"""

import sys
import unittest
from xbrl.cache import HttpCache
from xbrl.instance import parse_ixbrl, parse_xbrl, XbrlInstance, _normalize_transformed_value
import logging


# abs_file_path: str = str(os.path.dirname(os.path.abspath(inspect.getframeinfo(inspect.currentframe()).filename)))

class InstanceTest(unittest.TestCase):
    """
    Unit test for taxonomy.test_parse_taxonomy()
    """

    def test_parse_xbrl_document(self):
        """ Integration test for instance.parse_xbrl_instance() """
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        cache_dir: str = './cache/'
        cache: HttpCache = HttpCache(cache_dir)

        instance_doc_url: str = './tests/data/example.xml'
        inst: XbrlInstance = parse_xbrl(instance_doc_url, cache)
        print(inst)
        self.assertEqual(len(inst.facts), 1)

    def test_parse_ixbrl_document(self):
        """ Integration test for instance.parse_ixbrl_instance() """
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        cache_dir: str = './cache/'
        cache: HttpCache = HttpCache(cache_dir)

        instance_doc_url: str = './tests/data/example.html'
        inst: XbrlInstance = parse_ixbrl(instance_doc_url, cache)
        print(inst)
        self.assertEqual(len(inst.facts), 3)

    def test_normalize_transformed_value(self):
        test_transforms: [] = [
            # [format,value,expected]
            ['booleanfalse', 'no', 'false'],
            ['booleantrue', 'yeah', 'true'],

            ['datedaymonth', '2.12', '--12-02'],
            ['datedaymonthen', '2. December', '--12-02'],
            ['datedaymonthyear', '2.12.2021', '2021-12-02'],
            ['datedaymonthyearen', '02. December 2021', '2021-12-02'],
            ['datemonthday', '1.2', '--01-02'],
            ['datemonthdayen', 'Jan 02', '--01-02'],
            ['datemonthdayyear', '12-30-2021', '2021-12-30'],
            ['datemonthdayyearen', 'March 31, 2021', '2021-03-31'],
            ['dateyearmonthday', '2021.12.31', '2021-12-31'],

            ['nocontent', 'Bla bla', ''],
            ['numcommadecimal', '1.499,99', '1499.99'],
            ['numdotdecimal', '1,499.99', '1499.99'],

            ['zerodash', '-', '0'],
        ]
        for i, test_transform in enumerate(test_transforms):
            expected = test_transform[2]
            received = _normalize_transformed_value(test_transform[1], test_transform[0])
            self.assertEqual(expected, received, msg=f'Failed at test elem {i}')


if __name__ == '__main__':
    unittest.main()
