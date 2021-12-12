"""
This unittest tests the parsing of locally saved taxonomies
"""
import sys
import unittest
import logging

from xbrl.cache import HttpCache
from xbrl.taxonomy import parse_taxonomy, TaxonomySchema
from xbrl.helper.uri_helper import normalise_uri_dict, normalise_uri

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

        ns_to_taxonomy_LUT: dict = tax.get_taxonomy_LUT(dict())
        ns_to_taxonomy_LUT = normalise_uri_dict(ns_to_taxonomy_LUT)
        srt_tax: TaxonomySchema = ns_to_taxonomy_LUT.get(normalise_uri('http://fasb.org/srt/2020-01-31'), None)

        self.assertTrue(srt_tax)
        self.assertEqual(len(srt_tax.concepts), 489)

        # check if the labels where successfully linked to the concept
        self.assertEqual(len(tax.concepts['example_Assets'].labels), 2)


if __name__ == '__main__':
    unittest.main()
