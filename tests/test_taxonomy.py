import sys
import unittest
import os
import time
from xbrl_parser.cache import HttpCache
from xbrl_parser.taxonomy import parse_taxonomy, TaxonomySchema
import logging


class TaxonomySchemaTest(unittest.TestCase):
    """
    Unit test for taxonomy.test_parse_taxonomy()
    """

    def test_parse_taxonomy(self):
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        cache_dir: str = os.path.abspath('./../cache/') + '/'
        cache: HttpCache = HttpCache(cache_dir)
        print(f"Saving to {cache_dir}")

        """ Parse extending taxonomy of Apple Inc. and check if all us-gaap concepts where parsed """
        # extension_schema_url: str = 'https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/aapl-20200926.xsd'
        # tax: TaxonomySchema = parse_taxonomy(cache, extension_schema_url)
        # print(tax)
        # lei_tax: TaxonomySchema = tax.get_taxonomy('http://fasb.org/us-gaap/2020-01-31')
        # self.assertTrue(lei_tax)
        # self.assertEqual(len(lei_tax.concepts), 17281)
        # todo test with local test files


if __name__ == '__main__':
    unittest.main()
