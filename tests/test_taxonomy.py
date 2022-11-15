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

    @unittest.skip('跳過') 
    def test_parse_taxonomy(self):
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        from pathlib import Path
        
        extension_schema_path = (Path(__file__).parent / 'data/example.xsd').__str__()
        tax = parse_taxonomy(extension_schema_path)
        srt_tax: TaxonomySchema = tax.get_taxonomy('http://fasb.org/srt/2020-01-31')
        self.assertTrue(srt_tax)
        self.assertEqual(len(srt_tax.concepts), 489)

        # check if the labels where successfully linked to the concept
        self.assertEqual(len(tax.concepts['example_Assets'].labels), 2)

    def test_parse_tifrs_taxonomy(self):
        extension_schema_path = r'D:\tifrs\tifrs-20200630\BSCI\tifrs-bsci-bd-2020-06-30.xsd'
        t = parse_taxonomy(extension_schema_path)
        print(t.namespace)
        for p in t.pre_linkbases:
            print(p.treeview())
        # print(t.imports)    

if __name__ == '__main__':
    unittest.main()
