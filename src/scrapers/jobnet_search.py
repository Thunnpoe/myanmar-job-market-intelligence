from bs4 import BeautifulSoup
from src.scrapers.base import BaseScraper


class JobNetSearchScraper(BaseScraper):

    def get_job_urls(self, url):

        html = self.fetch(url)

        soup = BeautifulSoup(html, "lxml")

        job_urls = []

        links = soup.find_all("a", href=True)

        for link in links:

            href = link["href"]

            if href.startswith("/job/"):
                full_url = "https://www.jobnet.com.mm" + href

                if full_url not in job_urls:
                    job_urls.append(full_url)

        return job_urls