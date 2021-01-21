import logging
import sys
import unittest
import os
import time
from xbrl_parser.cache import HttpCache
from xbrl_parser.linkbase import parse_linkbase, Linkbase, LinkbaseType


class LinkbaseTest(unittest.TestCase):

    def test_parse_linkbase(self):
        """
        Unit test for linkbase.parse_linkbase()
        """
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        linkbase_url: str = 'https://www.esma.europa.eu/taxonomy/2019-03-27/esef_cor-lab-de.xml'
        cache_dir: str = os.path.abspath('./../cache/') + '/'
        cache: HttpCache = HttpCache(cache_dir)

        linkbase: Linkbase = parse_linkbase(cache, linkbase_url, LinkbaseType.LABEL)
        print(linkbase)
        # This linkbase has 5028 locators
        self.assertEqual(len(linkbase.extended_links[0].root_locators), 5028)
        # Todo: Function for getting all labels for a given concept id would be nice..
        # check the labels for one sample concept
        for locator in linkbase.extended_links[0].root_locators:
            if locator.concept_id != 'ifrs-full_Assets': continue
            label: str = locator.children[0].labels[0].text
            self.assertEqual(label, 'Vermögenswerte')


if __name__ == '__main__':
    unittest.main()
