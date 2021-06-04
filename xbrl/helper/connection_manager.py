from requests.adapters import HTTPAdapter
from urllib3.util import Retry

import requests
import time
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    This class handles http requests. If a requests fails, the method will retry the http requests as many times as specified.
    Between each requests the process will sleep {backoff factor} * (2 ** ({number of total retries} - 1)) seconds between
    failed requests. After the request is successful, the process will sleep delay / 1000 seconds so that it is
    compliant with sec's policy.

    https://www.sec.gov/privacy.htm#security

    """

    def __init__(self, delay: int = 500, retries: int = 5, backoff_factor: float = 0.8, headers: dict = None, logs =True):
        """

        @param from_locator: Specifies sleeping time after the request is successfull.
        @param retries: How many times a request will be tried before assuming its failure.
        @param backoff_factor: Used to measure time to sleep between failed requests.
            The formula used is {backoff factor} * (2 ** ({number of total retries} - 1))
        @param headers: Headers to use in http request.
        """
        self._delay = delay
        self._retries = retries
        self._backoff_factor = backoff_factor
        self._headers = headers
        self._session = self._create_session()
        self.logs = logs

    def download(self, url: str, headers: str):

        response = self._session.get(url, headers=headers, allow_redirects=True)
        if self.logs: logger.info(str(response.status_code) + " " + url)
        # Set a timeout, so that we do not get blocked by the for making to many requests
        time.sleep(self._delay / 1000)

        return response

    def _create_session(self,
                        status_forcelist: tuple = (500, 502, 503, 504, 403)) -> requests.Session:

        session = requests.Session()
        retry = Retry(
            total=self._retries,
            read=self._retries,
            connect=self._retries,
            backoff_factor=self._backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        return session
