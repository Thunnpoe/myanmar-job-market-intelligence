"""Parser for public MyJobs Myanmar search/detail pages.

Selectors are deliberately tolerant because the portal has changed markup over
time. This module never accesses candidate profiles or authenticated pages.
"""
from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper


class MyJobsScraper(BaseScraper):
    BASE_URL = "https://www.myjobs.com.mm"

    def get_job_urls(self, url):
        soup = BeautifulSoup(self.fetch(url), "lxml")
        urls = []
        for link in soup.select('a[href*="/job/"]'):
            href = link.get("href")
            if href:
                full = urljoin(self.BASE_URL, href)
                if full not in urls:
                    urls.append(full)
        return urls

    def get_all_job_urls(self, max_pages=200):
        urls = set()
        empty_pages = 0
        for page in range(1, max_pages + 1):
            before = len(urls)
            page_urls = self.get_job_urls(f"{self.BASE_URL}/jobs?page={page}")
            urls.update(page_urls)
            if len(urls) == before:
                empty_pages += 1
                if empty_pages >= 2:
                    break
            else:
                empty_pages = 0
        return sorted(urls)

    @staticmethod
    def _text(node):
        return node.get_text(" ", strip=True) if node else None

    def _label_value(self, soup, labels):
        labels = {label.lower() for label in labels}
        for node in soup.find_all(["dt", "th", "p", "span", "div", "strong"]):
            text = self._text(node)
            if not text or text.lower().rstrip(":") not in labels:
                continue
            sibling = node.find_next_sibling()
            value = self._text(sibling)
            if value and value.lower() not in labels:
                return value
        return None

    def scrape_job(self, url):
        soup = BeautifulSoup(self.fetch(url), "lxml")
        title = self._text(soup.find("h1"))
        company = None
        for selector in [".company-name", '[class*="company"]', 'a[href*="/company/"]']:
            company = self._text(soup.select_one(selector))
            if company:
                break
        description_node = soup.select_one(".job-description, .description, [class*='description']")
        description = self._text(description_node)
        return {
            "source": "myjobs",
            "url": url,
            "title": title,
            "company": company,
            "industry": self._label_value(soup, ["Industry", "Category"]),
            "location": self._label_value(soup, ["Location"]),
            "job_type": self._label_value(soup, ["Employment Type", "Job Type", "Work Type"]),
            "salary": self._label_value(soup, ["Salary"]),
            "experience": self._label_value(soup, ["Experience Length", "Experience"]),
            "education": self._label_value(soup, ["Qualification", "Education"]),
            "description": description,
            "posted_date_text": self._label_value(soup, ["Date Posted At", "Posted Date"]),
            "scraped_at": datetime.now(timezone.utc),
        }
