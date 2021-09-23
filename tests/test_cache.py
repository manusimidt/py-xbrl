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
        self.assertLess(time.time() - time_stamp, delay / 1000)

        # on the second execution the file path will be returned
        time_stamp = time.time()
        self.assertEqual(cache.cache_file(test_url), expected_path)
        self.assertLess(time.time() - time_stamp, delay / 1000)

        # test if the file was downloaded
        self.assertTrue(os.path.isfile(expected_path))
        # delete the file
        self.assertTrue(cache.purge_file(test_url))
        # test if the file was deleted
        self.assertFalse(os.path.isfile(expected_path))


if __name__ == '__main__':
    unittest.main()
