"""
This unittest tests the parsing of remotely saved taxonomies.
It needs a header to be able to execute. The unit tests will be skipped if no
http headers are provided
"""
import unittest
import logging
import sys
from xbrl.cache import HttpCache
from xbrl.taxonomy import TaxonomySchema, parse_taxonomy_url
from tests.utils import get_bot_header

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
cache: HttpCache = HttpCache('../cache/', delay=1500)
bot_header = get_bot_header()
# bot_header = get_bot_header('.env')
if bot_header: cache.set_headers(bot_header)


class RemoteTaxonomyTest(unittest.TestCase):
    """
    Unit tests for all http related parsing
    """

    @unittest.skipIf(bot_header is None, "Bot Header was not provided")
    def test_parse_taxonomy(self):
        """ Testing parsing xbrl submissions directly from the internet """
        schema_url: str = 'https://www.sec.gov/Archives/edgar/data/320193/000032019321000010/aapl-20201226.xsd'
        tax: TaxonomySchema = parse_taxonomy_url(schema_url, cache)
        self.assertEqual(len(tax.concepts), 65)
        us_gaap_tax: TaxonomySchema = tax.get_taxonomy('http://fasb.org/us-gaap/2020-01-31')
        self.assertEqual(len(us_gaap_tax.concepts), 17281)
        self.assertEqual(len(tax.concepts['aapl_MacMember'].labels), 3)


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
