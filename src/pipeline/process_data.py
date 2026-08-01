from src.database.mongo import (
    jobs_collection,
    processed_jobs_collection
)

from src.pipeline.clean import clean_job



jobs = jobs_collection.find()


count = 0


for job in jobs:

    cleaned_job = clean_job(job)


    processed_jobs_collection.update_one(
        {
            "url": cleaned_job["url"]
        },
        {
            "$set": cleaned_job
        },
        upsert=True
    )


    count += 1


print("Processed jobs:", count)
