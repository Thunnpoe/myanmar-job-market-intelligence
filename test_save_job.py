from src.scrapers.jobnet import JobNetScraper
from src.database.mongo import jobs_collection


url = "https://www.jobnet.com.mm/job/data-engineer-cb-bank/133661"


# Scrape job
scraper = JobNetScraper()

job = scraper.scrape_job(url)


# Save to MongoDB
result = jobs_collection.insert_one(job)


print("Saved job ID:", result.inserted_id)