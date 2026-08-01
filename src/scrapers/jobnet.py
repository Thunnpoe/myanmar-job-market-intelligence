from bs4 import BeautifulSoup
from src.scrapers.base import BaseScraper
from datetime import datetime, timezone


class JobNetScraper(BaseScraper):

    def scrape_job(self, url):

        html = self.fetch(url)

        soup = BeautifulSoup(html, "lxml")

        job = {
            "source": "jobnet",
            "url": url,
            "title": self.extract_title(soup),
            "company": self.extract_company(soup),
            "location": self.extract_location(soup),
            "experience": self.extract_detail(soup, "Experience level"),
            "job_function": self.extract_detail(soup, "Job Function"),
            "industry": self.extract_detail(soup, "Job Industry"),
            "education": self.extract_detail(soup, "Min Education Level"),
            "job_type": self.extract_detail(soup, "Job Type"),
            "description": self.extract_description(soup),
            "scraped_at": datetime.now(timezone.utc)
        }

        return job


    def extract_title(self, soup):

        title = soup.select_one(
            ".job-details__card-title"
        )

        if title:
            return title.text.strip()

        return None


    def extract_company(self, soup):

        company = soup.select_one(
            ".job-details__card-subtitle"
        )

        if company:
            return company.text.strip()

        return None


    def extract_location(self, soup):

        icon = soup.select_one(
            ".icon-cursor"
        )

        if icon:

            parent = icon.find_parent("div")

            if parent:

                span = parent.find("span")

                if span:
                    return span.text.strip()

        return None


    def extract_detail(self, soup, label):

        details = soup.select(
            ".job-details__showing"
        )

        for detail in details:

            title = detail.find("p")

            if title and title.text.strip() == label:

                value = detail.find("span")

                if value:
                    return value.text.strip()

        return None


    def extract_description(self, soup):

        description = soup.select_one(
            ".job-details__description-contant"
        )

        if description:

            return description.get_text(
                " ",
                strip=True
            )

        return None