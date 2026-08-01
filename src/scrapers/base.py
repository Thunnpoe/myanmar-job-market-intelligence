import time
import requests
from config.settings import REQUEST_DELAY


class BaseScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MyanmarJobMarketResearch/1.0"
        })

    def fetch(self, url):
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        time.sleep(REQUEST_DELAY)
        return response.text