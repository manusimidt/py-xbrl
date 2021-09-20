"""
This unittest tests the parsing of locally saved instance documents.
"""

import sys
import unittest
from xbrl.cache import HttpCache
from xbrl.instance import parse_ixbrl, parse_xbrl, XbrlInstance
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


if __name__ == '__main__':
    unittest.main()
