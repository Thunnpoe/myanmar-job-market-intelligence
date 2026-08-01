from src.scrapers.jobnet_search import JobNetSearchScraper
from src.scrapers.jobnet import JobNetScraper
from src.database.mongo import jobs_collection


keywords = [
    "engineer",
    "accountant",
    "marketing",
    "sales",
    "teacher",
    "customer service",
    "manager",
    "intern"
]


search_scraper = JobNetSearchScraper()
job_scraper = JobNetScraper()


all_job_urls = set()


# Collect job URLs from all keywords
for keyword in keywords:

    search_url = f"https://www.jobnet.com.mm/jobs?kw={keyword.replace(' ', '+')}"

    print("\nSearching:", keyword)

    job_urls = search_scraper.get_job_urls(search_url)

    print("Found:", len(job_urls), "jobs")

    all_job_urls.update(job_urls)



print("\nTotal unique jobs:", len(all_job_urls))


# Scrape jobs
for url in all_job_urls:

    try:

        print("\nScraping:", url)

        job = job_scraper.scrape_job(url)


# Skip invalid pages
        if not job["title"] or not job["company"]:
            print("Skipped invalid page:", url)
            continue


        jobs_collection.update_one(
            {
                "source": job["source"],
                "url": job["url"]
            },
            {
                "$set": job
            },
            upsert=True
        )


        print("Processed:", job["title"])


    except Exception as e:

        print("Failed:", url)
        print(e)