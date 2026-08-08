from src.database.mongo import jobs_collection, processed_jobs_collection
from src.pipeline.clean import clean_job
from src.pipeline.extract_skills import extract_skills


def process_jobs():
    count = 0
    for job in jobs_collection.find():
        cleaned_job = clean_job(job)
        cleaned_job["skills"] = extract_skills(cleaned_job)
        processed_jobs_collection.update_one(
            {"source": cleaned_job.get("source"), "url": cleaned_job.get("url")},
            {"$set": cleaned_job},
            upsert=True,
        )
        count += 1
    return count


def process_pending_jobs():
    """Process only raw jobs that are new or newer than their analyzed copy."""
    processed = {
        document["url"]: document.get("scraped_at")
        for document in processed_jobs_collection.find({}, {"url": 1, "scraped_at": 1})
        if document.get("url")
    }
    count = 0
    for job in jobs_collection.find():
        url = job.get("url")
        raw_time = job.get("scraped_at")
        processed_time = processed.get(url)
        if url in processed and (not raw_time or (processed_time and raw_time <= processed_time)):
            continue
        cleaned_job = clean_job(job)
        cleaned_job["skills"] = extract_skills(cleaned_job)
        cleaned_job.pop("_id", None)
        processed_jobs_collection.update_one(
            {"source": cleaned_job.get("source"), "url": url},
            {"$set": cleaned_job},
            upsert=True,
        )
        count += 1
    return count


if __name__ == "__main__":
    print("Processed jobs:", process_jobs())
