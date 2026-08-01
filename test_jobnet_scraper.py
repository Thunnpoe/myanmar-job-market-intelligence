from src.scrapers.jobnet import JobNetScraper


url = "https://www.jobnet.com.mm/job/data-engineer-cb-bank/133661"


scraper = JobNetScraper()

job = scraper.scrape_job(url)


for key, value in job.items():
    print("\n", key, ":", value)