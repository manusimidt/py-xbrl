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
        cache_dir: str = os.path.abspath('./../cache/') + '/'
        cache: HttpCache = HttpCache(cache_dir)

        # linkbase_url: str = 'https://www.esma.europa.eu/taxonomy/2019-03-27/esef_cor-lab-de.xml'
        # linkbase: Linkbase = parse_linkbase(cache, linkbase_url, LinkbaseType.LABEL)
        # todo: Test linkbase from local files


if __name__ == '__main__':
    unittest.main()
