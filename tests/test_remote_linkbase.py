"""
This unittest tests the parsing of remotely saved linkbases.
It needs a header to be able to execute. The unit tests will be skipped if no
http headers are provided
"""
import unittest
import logging
import sys
from xbrl_parser.cache import HttpCache
from xbrl_parser.linkbase import parse_linkbase_url, LinkbaseType, Linkbase, Locator, Label
from tests.utils import get_bot_header

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
cache: HttpCache = HttpCache('../cache/', delay=1500)
bot_header = get_bot_header()
if bot_header: cache.set_headers(bot_header)


class RemoteLinkbaseTest(unittest.TestCase):

    @unittest.skipIf(bot_header is None, "Bot Header was not provided")
    def test_parse_linkbase_url(self):
        """ Testing parsing xbrl submissions directly from the internet """
        linkbase_url: str = 'https://www.esma.europa.eu/taxonomy/2019-03-27/esef_cor-lab-de.xml'
        linkbase: Linkbase = parse_linkbase_url(linkbase_url, LinkbaseType.LABEL, cache)
        self.assertEqual(len(linkbase.extended_links), 1)
        self.assertEqual(len(linkbase.extended_links[0].root_locators), 5028)
        assets_locator: Locator = next(filter(lambda x: x.name == 'Assets', linkbase.extended_links[0].root_locators))
        assets_label: Label = assets_locator.children[0].labels[0]
        self.assertEqual(assets_label.text, 'Vermögenswerte')


if __name__ == '__main__':
    """
    This script should not be triggered by GitHub Actions, since it relies on downloading huge files from external servers.
    If you want to run the test on your machine, please create a .env file and provide a parameter "USER_AGENT".

    This script downloads submissions from SEC EDGAR. The SEC requires you to identify and classify your bot by
    providing a User-Agent and a FROM header to your http request.
    https://www.sec.gov/privacy.htm#security
    """
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    headers = get_bot_header()
    if headers:
        cache.set_headers(headers)
        unittest.main()
    else:
        print("Skipping remote instance test. Reason: Could not load FROM and/or USER_AGENT attributes from .env file")
        exit(0)
