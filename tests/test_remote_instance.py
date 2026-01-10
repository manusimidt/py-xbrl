"""
This unittest tests the parsing of remotely saved instance documents.
It needs a header to be able to execute. The unit tests will be skipped if no
http headers are provided
"""

import unittest
import logging
import sys
from xbrl.cache import HttpCache
from xbrl.instance import parse_xbrl_url, parse_ixbrl_url, XbrlInstance
from tests.utils import get_bot_header

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
cache: HttpCache = HttpCache("../cache/", delay=1500)
bot_header = get_bot_header()
if bot_header:
    cache.set_headers(bot_header)


class RemoteInstanceTest(unittest.TestCase):
    """
    Unit tests for all http related parsing
    """

    @unittest.skipIf(bot_header is None, "Bot Header was not provided")
    def test_xbrl(self):
        """Testing parsing xbrl submissions directly from the internet"""
        instance_url: str = "https://www.sec.gov/Archives/edgar/data/320193/000032019318000007/aapl-20171230.xml"
        inst: XbrlInstance = parse_xbrl_url(instance_url, cache)
        # Looking at the document, this instance document has 274 contexts defined
        self.assertEqual(len(inst.context_map), 274)
        # Looking at the document, this instance document has 8 units defined
        self.assertEqual(len(inst.unit_map), 8)

    @unittest.skipIf(bot_header is None, "Bot Header was not provided")
    def test_ixbrl(self):
        """Testing parsing xbrl submissions directly from the internet"""
        instance_url: str = "https://www.sec.gov/Archives/edgar/data/320193/000032019321000010/aapl-20201226.htm"
        inst: XbrlInstance = parse_ixbrl_url(instance_url, cache)
        self.assertEqual(len(inst.context_map), 207)
        self.assertEqual(len(inst.unit_map), 9)


if __name__ == "__main__":
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
        print(
            "Skipping remote instance test. Reason: Could not load FROM and/or USER_AGENT attributes from .env file"
        )
        exit(0)
