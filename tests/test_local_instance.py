import sys
import unittest
import os
import time
from xbrl_parser.cache import HttpCache
from xbrl_parser.instance import parse_ixbrl, parse_xbrl, XbrlInstance
from xbrl_parser.taxonomy import parse_taxonomy, TaxonomySchema
import logging


class TaxonomySchemaTest(unittest.TestCase):
    """
    Unit test for taxonomy.test_parse_taxonomy()
    """

    def test_parse_xbrl_document(self):
        """ Integration test for instance.parse_xbrl_instance() """
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        cache_dir: str = os.path.abspath('./../cache/') + '/'
        cache: HttpCache = HttpCache(cache_dir)

        instance_doc_url: str = os.path.abspath('./data/example.xml')
        inst: XbrlInstance = parse_xbrl(instance_doc_url, cache)
        print(inst)
        self.assertEqual(len(inst.facts), 1)

    def test_parse_ixbrl_document(self):
        """ Integration test for instance.parse_ixbrl_instance() """
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        cache_dir: str = os.path.abspath('./../cache/') + '/'
        cache: HttpCache = HttpCache(cache_dir)

        instance_doc_url: str = os.path.abspath('./data/example.html')
        inst: XbrlInstance = parse_ixbrl(instance_doc_url, cache)
        print(inst)
        self.assertEqual(len(inst.facts), 3)


if __name__ == '__main__':
    unittest.main()
