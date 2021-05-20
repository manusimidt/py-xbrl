"""
This unittest tests the parsing of locally saved taxonomies
"""
import sys
import unittest
import os
from xbrl_parser.cache import HttpCache
from xbrl_parser.taxonomy import parse_taxonomy, TaxonomySchema
import logging


class TaxonomySchemaTest(unittest.TestCase):
    """
    Unit test for taxonomy.test_parse_taxonomy()
    """

    def test_parse_taxonomy(self):
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        cache_dir: str = os.path.abspath('./cache/') + '/'
        cache: HttpCache = HttpCache(cache_dir)
        print(f"Saving to {cache_dir}")

        extension_schema_path: str = os.path.abspath('./tests/data/example.xsd')
        tax: TaxonomySchema = parse_taxonomy(extension_schema_path, cache)
        print(tax)
        srt_tax: TaxonomySchema = tax.get_taxonomy('http://fasb.org/srt/2020-01-31')
        self.assertTrue(srt_tax)
        self.assertEqual(len(srt_tax.concepts), 489)


if __name__ == '__main__':
    unittest.main()
