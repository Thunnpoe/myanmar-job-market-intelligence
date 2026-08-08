from src.scrapers.jobnet_search import JobNetSearchScraper
from src.scrapers.jobnet import JobNetScraper
from src.scrapers.myjobs import MyJobsScraper
from src.database.mongo import jobs_collection, processed_jobs_collection, ensure_indexes
from config.settings import MAX_LISTING_PAGES, REFRESH_AFTER_HOURS, INACTIVE_AFTER_DAYS
from src.pipeline.clean import clean_job
from src.pipeline.extract_skills import extract_skills
from datetime import datetime, timedelta, timezone

KEYWORDS = ["engineer", "accountant", "marketing", "sales", "teacher",
            "customer service", "manager", "intern"]


def save_jobs(scraper, urls, resume=True):
    saved = 0
    failed = 0
    urls = list(urls)
    source = scraper_source(scraper)
    sync_time = datetime.now(timezone.utc)
    stale_cutoff = sync_time - timedelta(hours=REFRESH_AFTER_HOURS)

    synchronized = synchronize_existing(source)
    if synchronized:
        print(f"Synchronized existing {source} jobs: {synchronized}")

    fresh_urls = set()
    if resume and urls:
        for document in jobs_collection.find(
            {"source": source, "url": {"$in": urls}},
            {"url": 1, "scraped_at": 1},
        ):
            scraped_at = document.get("scraped_at")
            if scraped_at and scraped_at.tzinfo is None:
                scraped_at = scraped_at.replace(tzinfo=timezone.utc)
            if scraped_at and scraped_at >= stale_cutoff:
                fresh_urls.add(document["url"])

    # A listing/sitemap appearance confirms the posting was seen this run.
    jobs_collection.update_many(
        {"source": source, "url": {"$in": urls}},
        {"$set": {"last_seen_at": sync_time, "is_active": True}},
    )
    processed_jobs_collection.update_many(
        {"source": source, "url": {"$in": urls}},
        {"$set": {"last_seen_at": sync_time, "is_active": True}},
    )

    pending_urls = [url for url in urls if url not in fresh_urls]
    skipped = len(urls) - len(pending_urls)
    print(f"Fresh existing jobs: {skipped}; new/stale details: {len(pending_urls)}")

    for position, url in enumerate(pending_urls, start=1):
        try:
            job = scraper.scrape_job(url)
            if not job.get("title"):
                failed += 1
                continue
            job["last_seen_at"] = sync_time
            job["is_active"] = True
            jobs_collection.update_one(
                {"source": job["source"], "url": job["url"]},
                {"$set": job}, upsert=True,
            )

            cleaned_job = clean_job(dict(job))
            cleaned_job["skills"] = extract_skills(cleaned_job)
            processed_jobs_collection.update_one(
                {"source": cleaned_job["source"], "url": cleaned_job["url"]},
                {"$set": cleaned_job}, upsert=True,
            )
            saved += 1
            if position == 1 or position % 25 == 0 or position == len(pending_urls):
                print(
                    f"Progress: {position}/{len(pending_urls)}; "
                    f"saved/refreshed: {saved}; failed: {failed}"
                )
        except Exception as error:
            failed += 1
            print("Failed:", url, error)

    inactive_cutoff = sync_time - timedelta(days=INACTIVE_AFTER_DAYS)
    inactive_query = {
        "source": source,
        "url": {"$nin": urls},
        "last_seen_at": {"$lt": inactive_cutoff},
        "is_active": {"$ne": False},
    }
    deactivated = jobs_collection.update_many(
        inactive_query,
        {"$set": {"is_active": False, "inactive_at": sync_time}},
    ).modified_count
    processed_jobs_collection.update_many(
        inactive_query,
        {"$set": {"is_active": False, "inactive_at": sync_time}},
    )
    return {
        "saved_or_refreshed": saved,
        "fresh_skipped": skipped,
        "failed": failed,
        "deactivated": deactivated,
    }


def synchronize_existing(source):
    """Ensure previously downloaded raw jobs are available to the dashboard."""
    count = 0
    for job in jobs_collection.find({"source": source}):
        cleaned_job = clean_job(dict(job))
        cleaned_job["skills"] = extract_skills(cleaned_job)
        processed_jobs_collection.update_one(
            {"source": cleaned_job["source"], "url": cleaned_job["url"]},
            {"$set": cleaned_job}, upsert=True,
        )
        count += 1
    return count


def scraper_source(scraper):
    if isinstance(scraper, JobNetScraper):
        return "jobnet"
    if isinstance(scraper, MyJobsScraper):
        return "myjobs"
    raise ValueError(f"Unknown scraper type: {type(scraper).__name__}")


def collect_jobnet():
    search = JobNetSearchScraper()
    scraper = JobNetScraper()
    urls = set(search.get_all_job_urls(MAX_LISTING_PAGES))
    # Keep keyword searches as a fallback for older/filtered listing routes.
    if not urls:
        for keyword in KEYWORDS:
            url = f"https://www.jobnet.com.mm/jobs?kw={keyword.replace(' ', '+')}"
            urls.update(search.get_job_urls(url))
    print("JobNet unique URLs:", len(urls))
    return save_jobs(scraper, urls)


def collect_myjobs(pages=1):
    scraper = MyJobsScraper()
    if pages is None:
        pages = MAX_LISTING_PAGES
    urls = set(scraper.get_all_job_urls(pages))
    print("MyJobs unique URLs:", len(urls))
    return save_jobs(scraper, urls)


if __name__ == "__main__":
    ensure_indexes()
    print("JobNet saved:", collect_jobnet())
    print("MyJobs saved:", collect_myjobs(MAX_LISTING_PAGES))
