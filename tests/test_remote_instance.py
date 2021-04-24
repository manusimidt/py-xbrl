import unittest
import logging
import sys
from xbrl_parser.cache import HttpCache
from xbrl_parser.instance import parse_xbrl_url, parse_ixbrl_url, XbrlInstance

cache: HttpCache = HttpCache('../cache/', delay=1500)


class RemoteInstanceTest(unittest.TestCase):
    # class RemoteInstanceTest:
    """
    Unit tests for all http related parsing
    """

    def test_xbrl(self):
        """ Testing parsing xbrl submissions directly from the internet """
        instance_url: str = 'https://www.sec.gov/Archives/edgar/data/320193/000032019318000007/aapl-20171230.xml'
        inst: XbrlInstance = parse_xbrl_url(instance_url, cache)
        self.assertEqual(len(inst.context_map), 274)
        self.assertEqual(len(inst.unit_map), 10)

    def test_ixbrl(self):
        """ Testing parsing xbrl submissions directly from the internet """
        instance_url: str = 'https://www.sec.gov/Archives/edgar/data/320193/000032019321000010/aapl-20201226.htm'
        inst: XbrlInstance = parse_xbrl_url(instance_url, cache)
        self.assertEqual(len(inst.context_map), 207)
        self.assertEqual(len(inst.unit_map), 11)


if __name__ == '__main__':
    """
    This script should not be triggered by GitHub Actions, since it relies on downloading huge files from external servers.
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
            cache.set_headers({
                'From': from_header,
                'User-Agent': user_agent_header
            })
            unittest.main()
        else:
            print("Skipping remote instance test. Reason: .env file either missing FROM or USER_AGENT attribute")
            exit(0)
    except FileNotFoundError as e:
        print("Skipping remote instance test. Reason: No .env file provided")
        exit(0)
