"""
This is just a very simple unit test, that checks if the HttpCache is able to download a file, save it in the
specified cache directory and serves it from there.
"""

import sys
import unittest
import os
import time
from xbrl.cache import HttpCache
import logging


class CacheHelperTest(unittest.TestCase):

    def test_cache_file(self):
        """
        Unit test for CacheHelper.cache_file
        :return:
        """
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        cache_dir: str = os.path.abspath('./../cache/') + '/'
        delay: int = 5000
        cache: HttpCache = HttpCache(cache_dir, delay)

        test_url: str = "https://www.w3schools.com/xml/note.xml"
        expected_path: str = cache_dir + "www.w3schools.com/xml/note.xml"

        # if the testing file already exists delete if first
        if os.path.isfile(expected_path):
            os.remove(expected_path)

        # on the first execution the file will be downloaded from the internet, no delay for first download
        time_stamp: float = time.time()
        self.assertEqual(cache.cache_file(test_url), expected_path)
        time_delta = time.time() - time_stamp
        self.assertLess(time_delta, delay / 1000)
        logging.info(f"Time delta for first download: {time_delta}ms")

        # delete the file and download it again to check if the delay for the second download is working
        self.assertTrue(cache.purge_file(test_url))

        time_stamp: float = time.time()
        self.assertEqual(cache.cache_file(test_url), expected_path)
        time_delta = time.time() - time_stamp
        self.assertGreaterEqual(time_delta, delay / 1000)
        logging.info(f"Time delta for second download: {time_delta}ms")

        # now that the file is cached on the hard drive, the file path should be returned immediately
        time_stamp = time.time()
        self.assertEqual(cache.cache_file(test_url), expected_path)
        time_delta = time.time() - time_stamp
        self.assertLess(time_delta, delay / 1000)
        logging.info(f"Time delta for third download: {time_delta}ms")

        # test if the file was downloaded
        self.assertTrue(os.path.isfile(expected_path))
        # delete the file
        self.assertTrue(cache.purge_file(test_url))
        # test if the file was deleted
        self.assertFalse(os.path.isfile(expected_path))


if __name__ == '__main__':
    unittest.main()
