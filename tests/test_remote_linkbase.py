import unittest
import logging
import sys
from xbrl_parser.cache import HttpCache
from xbrl_parser.linkbase import parse_linkbase_url, LinkbaseType, Linkbase, Locator, Label

cache: HttpCache = HttpCache('../cache/', delay=1500)


class RemoteLinkbaseTest(unittest.TestCase):

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
    This script should not be triggered by GitHub Actions, since it relies on downloading files from external servers.
    If you want to run the test on your machine, please create a .env file and provide a parameter "USER_AGENT".
    
    This script downloads submissions from SEC EDGAR. The SEC requires you to identify and classify your bot by
    providing a User-Agent and a FROM header to your http request.
    https://www.sec.gov/privacy.htm#security
    """
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    try:
        f = open(".env", "r")
        from_header: str or None = None
        user_agent_header: str or None = None
        for line in f:
            env_name, env_value = [x.strip() for x in line.strip().split('=')]
            if env_name == 'FROM':
                from_header = env_value
            elif env_name == 'USER_AGENT':
                user_agent_header = env_value
        if from_header and user_agent_header:
            # cache.set_headers({
            #     'From': from_header,
            #     'User-Agent': user_agent_header
            # })
            unittest.main()
        else:
            print("Skipping remote instance test. Reason: .env file either missing FROM or USER_AGENT attribute")
            exit(0)
    except FileNotFoundError as e:
        print("Skipping remote instance test. Reason: No .env file provided")
        exit(0)
