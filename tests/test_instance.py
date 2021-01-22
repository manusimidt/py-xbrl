import sys
import unittest
import os
import time
from xbrl_parser.cache import HttpCache
from xbrl_parser.instance import parse_ixbrl_instance, parse_xbrl_instance, XbrlInstance
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
        """ Integration test for instance.parse_xbrl_instance() """
        instance_doc_url: str = 'https://www.sec.gov/Archives/edgar/data/320193/000032019318000007/aapl-20171230.xml'
        inst: XbrlInstance = parse_xbrl_instance(cache, instance_doc_url)
        print(inst)
        self.assertEqual(len(inst.facts), 882)

    def test_parse_ixbrl_document(self):
        """ Integration test for instance.parse_ixbrl_instance() """
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        cache_dir: str = os.path.abspath('./../cache/') + '/'
        cache: HttpCache = HttpCache(cache_dir)
        """ Integration test for instance.parse_ixbrl_instance() """
        instance_doc_url: str = 'https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/aapl-20200926.htm'
        inst: XbrlInstance = parse_ixbrl_instance(cache, instance_doc_url)
        print(inst)
        self.assertEqual(len(inst.facts), 1334)


if __name__ == '__main__':
    unittest.main()
