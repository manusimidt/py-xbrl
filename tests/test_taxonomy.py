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

        """ Parse ESEF taxonomy and check if lei was also imported """

        # entry point for ESEF core schema
        entry_point_url: str = 'https://www.esma.europa.eu/taxonomy/2019-03-27/esef_cor.xsd'

        tax: TaxonomySchema = parse_taxonomy(cache, entry_point_url)
        # test if the lei taxonomy was also parsed (the lei taxonomy is imported by ESEF)
        lei_tax: TaxonomySchema = tax.get_taxonomy('http://www.xbrl.org/taxonomy/int/lei/2018-11-01')
        self.assertTrue(lei_tax)

        """ Parse extending taxonomy of Apple Inc. and check if all us-gaap concepts where parsed """
        extension_schema_url: str = 'https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/aapl-20200926.xsd'

        tax: TaxonomySchema = parse_taxonomy(cache, extension_schema_url)
        print(tax)
        lei_tax: TaxonomySchema = tax.get_taxonomy('http://fasb.org/us-gaap/2020-01-31')
        self.assertTrue(lei_tax)
        # us-gaap 2020 has 17281 concepts
        self.assertEqual(len(lei_tax.concepts), 17281)


if __name__ == '__main__':
    unittest.main()
