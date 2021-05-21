"""
This unittest tests the parsing of locally saved linkbases
"""
import unittest
from xbrl_parser.linkbase import parse_linkbase, Linkbase, LinkbaseType


class LinkbaseTest(unittest.TestCase):

    def test_label_linkbase(self):
        """
        Unit test for linkbase.parse_linkbase()
        """
        linkbase_path: str = './tests/data/example-lab.xml'
        linkbase: Linkbase = parse_linkbase(linkbase_path, LinkbaseType.LABEL)

        self.assertEqual(len(linkbase.extended_links), 1)
        self.assertEqual(linkbase.extended_links[0].root_locators[0].name, 'loc_Assets')
        label_arcs = linkbase.extended_links[0].root_locators[0].children
        self.assertEqual(label_arcs[0].labels[0].text, 'Assets, total')
        self.assertIn('An asset is a resource with economic value', label_arcs[1].labels[0].text)

    def test_calculation_linkbase(self):
        """
        Unit test for linkbase.parse_linkbase()
        """
        linkbase_path: str = './tests/data/example-cal.xml'
        linkbase: Linkbase = parse_linkbase(linkbase_path, LinkbaseType.CALCULATION)

        assets_locator = linkbase.extended_links[0].root_locators[0]
        # test if the exploratory mathematical relationship between assets, non-current assets and current assets
        # was present in the linkbase
        self.assertEqual(assets_locator.concept_id, 'example_Assets')
        self.assertEqual(assets_locator.children[0].to_locator.concept_id, 'example_NonCurrentAssets')
        self.assertEqual(assets_locator.children[1].to_locator.concept_id, 'example_CurrentAssets')


if __name__ == '__main__':
    unittest.main()
