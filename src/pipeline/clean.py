import re


def clean_text(value):

    if not value:
        return None

    return value.strip()


def clean_location(location):

    if not location:
        return None

    location = location.lower()

    if "yangon" in location:
        return "Yangon"

    if "mandalay" in location:
        return "Mandalay"

    return location.title()



def clean_job_type(job_type):

    if not job_type:
        return None

    job_type = job_type.lower()

    if "full" in job_type:
        return "Full Time"

    if "part" in job_type:
        return "Part Time"

    if "intern" in job_type:
        return "Internship"

    if "contract" in job_type:
        return "Contract"

    return job_type.title()



def clean_experience(experience):

    if not experience:
        return None

    experience = experience.lower()

    if "entry" in experience or "junior" in experience:
        return "Junior"

    if "experienced" in experience or "senior" in experience:
        return "Senior"

    if "manager" in experience:
        return "Manager"

    return "Not specified"



def clean_job(job):

    job["title"] = clean_text(job.get("title"))
    job["company"] = clean_text(job.get("company"))

    job["city"] = clean_location(
        job.get("location")
    )

    job["job_type_clean"] = clean_job_type(
        job.get("job_type")
    )

    job["experience_level"] = clean_experience(
        job.get("experience")
    )

    return job