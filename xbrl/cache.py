"""
Downloads files and stores them locally.
"""
import os
import re
import zipfile
from pathlib import Path

from xbrl.helper.connection_manager import ConnectionManager


class HttpCache:
    """
    Simple persistent HTTP cache. Requests files over http and stores them into the cache. Just returns
    the file path if the same file is requested twice. Also automatically handles retries when request fails.
    """

    def __init__(self, cache_dir: str, delay: int = 500, verify_https: bool = True):
        """
        :param cache_dir: Root directory of the disk cache (all requested files will be cached in this directory)
        :param delay: Minimum time in milliseconds between two requests
        :param verify_https: Disable SSL certificate validation for speed up (see https://github.com/manusimidt/py-xbrl/pull/57)
        """
        # check if the cache_dir ends with a /
        if not cache_dir.endswith('/'): cache_dir += '/'
        self.cache_dir: str = cache_dir
        self.headers: dict or None = None
        self.connection_manager = ConnectionManager(delay, verify_https=verify_https)

    def set_headers(self, headers: dict) -> None:
        """
        Sets the header for all following request

        :param headers: python dictionary with string key and value
        Example header:

        .. code-block:: json

            {
                "From": "pete.smith@example.com",
                "User-Agent" : "ExampleBot/1.0 (https.example.com/exampleBot)"
            }
        """
        self.headers = headers
        self.connection_manager._headers = headers

    def set_connection_params(self, delay: int = 500, retries: int = 5, backoff_factor: float = 0.8,
                              logs: bool = True) -> None:
        """
        Sets the connection params for all following request

        :param delay: Minimum time in milliseconds between two requests
        :param retries: int specifying how many times a request will be tried before assuming its failure.
        :param backoff_factor: Used to measure time to sleep between failed requests. The formula used is:
            {backoff factor} * (2 ** ({number of total retries} - 1))
        :param logs: enables or disables download logs
        """
        self.connection_manager._delay_ms = delay
        self.connection_manager._retries = retries
        self.connection_manager._backoff_factor = backoff_factor
        self.connection_manager.logs = logs

    def cache_file(self, file_url: str) -> str:
        """
        Caches a file in the http cache.

        :param file_url: url (https link) to the file to be cached.
        :return: returns the absolute path to the cached file
        """
        file_path: str = self.url_to_path(file_url)
        # first check if the files
        if os.path.exists(file_path):
            return file_path

        file_dir_path: str = '/'.join(file_path.split('/')[0:-1])
        # try to download the file
        if not os.path.isdir(file_dir_path):
            os.makedirs(file_dir_path)

        query_response = self.connection_manager.download(file_url, headers=self.headers)

        if not query_response.status_code == 200:
            if query_response.status_code == 404:
                raise Exception(
                    "Could not find file on {}. Error code: {}".format(file_url, query_response.status_code))
            else:
                raise Exception(
                    "Could not download file from {}. Error code: {}".format(file_url, query_response.status_code))

        with open(file_path, "wb+") as file:
            file.write(query_response.content)
            file.close()

        return file_path

    def purge_file(self, file_url: str) -> bool:
        """
        Removes a file from the cache

        :param file_url: url (https link) to the file to be deleted.
        :return: true if the file was deleted, false if it could not be found
        """
        try:
            os.remove(self.url_to_path(file_url))
        except FileNotFoundError:
            return False
        return True

    def url_to_path(self, url: str) -> str:
        """
        Takes a url and converts it to the absolute local cache path

        :param url: url of the file you want to know the cache path
        :return: absolute local cache path
        """
        return self.cache_dir + re.sub("https?://", "", url)

    def cache_edgar_enclosure(self, enclosure_url: str) -> str:
        """
        Downloads the ZIP folder, extracts it and stores the files in the cache.

        :param enclosure_url: url to the zip folder.
        :return: relative path to extracted zip's content
        """
        # todo: why is it called "cache_edgar_enclosure" you could theoretically cache any zip enclosure.
        if not enclosure_url.endswith('.zip'):
            raise Exception("This is not a valid zip folder")
        # download the zip folder and store it into the default http cache
        enclosure_path = self.cache_file(file_url=enclosure_url)
        submission_dir_path = self.url_to_path('/'.join(enclosure_url.split('/')[:-1]))
        # extract the zip folder
        with zipfile.ZipFile(enclosure_path, "r") as zip_ref:
            zip_ref.extractall(submission_dir_path)
            zip_ref.close()
        return submission_dir_path

    @DeprecationWarning
    def find_entry_file(self, dir_path: str) -> str or None:
        """
        NOTE: This function only works for enclosed SEC submissions that where already downloaded!
        Also this function does only return the most likely file path for the instance document.
        If you want to be certain i would recommend to use the SEC Structured Disclosure RSS Feeds
        https://www.sec.gov/structureddata/rss-feeds-submitted-filings
        These rss feeds list all files per submission and gives you information about the filetype (instance document,
        taxonomy schema, label linkbase, exhibit e.t.c)

        Find the most likely entry file in provided filling directory
        """

        # filter for files in interest
        valid_files = []
        for ext in '.htm .xml .xsd'.split():  # valid extensions in priority
            for f in os.listdir(dir_path):
                f_full = os.path.join(dir_path, f)
                if os.path.isfile(f_full) and f.lower().endswith(ext):
                    valid_files.append(f_full)

        # find first file which is not included by others
        entry_candidates = []
        for file1 in valid_files:
            f_dir, file_nm = os.path.split(file1)
            # foreach file check all other for inclusion
            found_in_other = False
            for file2 in valid_files:
                if file1 != file2:
                    if file_nm in Path(file2).read_text():
                        found_in_other = True
                        break

            if not found_in_other:
                entry_candidates.append((file1, os.path.getsize(file1)))

        # if multiple choose biggest
        entry_candidates.sort(key=lambda tup: tup[1], reverse=True)
        if len(entry_candidates) > 0:
            file_path, size = entry_candidates[0]
            return file_path
        return None
