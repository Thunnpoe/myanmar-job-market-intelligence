from bs4 import BeautifulSoup
from src.scrapers.base import BaseScraper
from urllib.parse import urljoin
import re
import xml.etree.ElementTree as ET


class JobNetSearchScraper(BaseScraper):

    def get_sitemap_urls_from_robots(self):
        """Read the site's currently advertised sitemap URLs."""
        robots = self.fetch("https://www.jobnet.com.mm/robots.txt")
        return [
            line.split(":", 1)[1].strip()
            for line in robots.splitlines()
            if line.lower().startswith("sitemap:") and ":" in line
        ]

    def get_job_urls(self, url):

        html = self.fetch(url)

        soup = BeautifulSoup(html, "lxml")

        job_urls = []

        links = soup.find_all("a", href=True)

        for link in links:

            href = link["href"]

            if "/job/" in href:
                full_url = urljoin("https://www.jobnet.com.mm", href)

                if full_url not in job_urls:
                    job_urls.append(full_url)

        return job_urls

    def get_sitemap_job_urls(self, sitemap_url):
        """Return public job URLs from a sitemap or sitemap index."""
        body = self.fetch(sitemap_url)
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            return []
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [node.text.strip() for node in root.findall(".//sm:loc", ns) if node.text]
        # Sitemap indexes point to child XML files; normal sitemaps point to URLs.
        if root.tag.lower().endswith("sitemapindex"):
            urls = []
            for child in locs:
                urls.extend(self.get_sitemap_job_urls(child))
            return urls
        return [url for url in locs if re.search(r"/job/", url, re.I)]

    def get_all_job_urls(self, max_pages=200):
        """Use official sitemaps first, then cautiously walk listing pages."""
        urls = set()
        try:
            sitemap_urls = self.get_sitemap_urls_from_robots()
        except Exception as error:
            print("Robots sitemap list unavailable:", error)
            sitemap_urls = [
                "https://www.jobnet.com.mm/sitemap_1.xml",
                "https://www.jobnet.com.mm/sitemap_2.xml",
            ]
        for sitemap in sitemap_urls:
            try:
                urls.update(self.get_sitemap_job_urls(sitemap))
            except Exception as error:
                print("Sitemap unavailable:", sitemap, error)

        # The listing currently exposes a public total and page links. Stop after
        # two pages with no new URLs to avoid hammering a changed endpoint.
        empty_pages = 0
        for page in range(1, max_pages + 1):
            before = len(urls)
            listing = "https://www.jobnet.com.mm/jobs-in-myanmar" if page == 1 else f"https://www.jobnet.com.mm/jobs-in-myanmar?page={page}"
            try:
                urls.update(self.get_job_urls(listing))
            except Exception as error:
                print("Listing unavailable:", listing, error)
                break
            if len(urls) == before:
                empty_pages += 1
                if empty_pages >= 2:
                    break
            else:
                empty_pages = 0
        return sorted(urls)
