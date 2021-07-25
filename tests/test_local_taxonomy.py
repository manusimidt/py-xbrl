"""
This unittest tests the parsing of locally saved taxonomies
"""
import sys
import unittest
from xbrl.cache import HttpCache
from xbrl.taxonomy import parse_taxonomy, TaxonomySchema
import logging


class TaxonomySchemaTest(unittest.TestCase):
    """
    Unit test for taxonomy.test_parse_taxonomy()
    """

    def test_parse_taxonomy(self):
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        cache_dir: str = './cache/'
        cache: HttpCache = HttpCache(cache_dir)
        print(f"Saving to {cache_dir}")

        extension_schema_path: str = './tests/data/example.xsd'
        # extension_schema_path: str = './data/example.xsd'
        tax: TaxonomySchema = parse_taxonomy(extension_schema_path, cache)
        print(tax)
        srt_tax: TaxonomySchema = tax.get_taxonomy('http://fasb.org/srt/2020-01-31')
        self.assertTrue(srt_tax)
        self.assertEqual(len(srt_tax.concepts), 489)

        # check if the labels where successfully linked to the concept
        self.assertEqual(len(tax.concepts['example_Assets'].labels), 2)


if __name__ == '__main__':
    unittest.main()
