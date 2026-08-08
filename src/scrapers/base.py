import time
import requests
from config.settings import REQUEST_DELAY, USER_AGENT


class BaseScraper:
    def __init__(self, delay=None):
        self.delay = REQUEST_DELAY if delay is None else delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.8",
        })

    def fetch(self, url):
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        time.sleep(self.delay)
        return response.text
