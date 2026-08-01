from src.database.mongo import processed_jobs_collection
from src.pipeline.extract_skills import extract_skills


jobs = processed_jobs_collection.find()


count = 0


for job in jobs:

    skills = extract_skills(job)


    processed_jobs_collection.update_one(
        {
            "_id": job["_id"]
        },
        {
            "$set": {
                "skills": skills
            }
        }
    )


    count += 1


print("Skill extraction completed:", count)