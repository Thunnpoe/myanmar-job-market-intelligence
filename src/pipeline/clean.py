import re
from datetime import datetime, timezone


def clean_text(value):

    if not value:
        return None

    return re.sub(r"\s+", " ", str(value)).strip()


def clean_location(location):

    if not location:
        return None

    location = location.lower()

    if "yangon" in location:
        return "Yangon"

    if "mandalay" in location:
        return "Mandalay"

    if "nay pyi taw" in location or "naypyidaw" in location:
        return "Nay Pyi Taw"
    if "ပဲခူး" in location or "bago" in location:
        return "Bago"
    if "မော်လမြိုင်" in location or "mawlamyine" in location:
        return "Mawlamyine"
    if "ပုသိမ်" in location or "pathein" in location:
        return "Pathein"

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

    if "experienced" in experience or "senior" in experience or "mid" in experience:
        return "Senior"

    if "manager" in experience:
        return "Manager"

    return "Not specified"


def clean_education(education):
    value = clean_text(education)
    if not value:
        return "Not specified"
    value = value.lower()
    if "master" in value or "mba" in value:
        return "Master's"
    if "bachelor" in value or "degree" in value:
        return "Bachelor's"
    if "diploma" in value or "certificate" in value:
        return "Diploma"
    if "high school" in value or "matric" in value:
        return "High school"
    return "Other"


def parse_experience_years(value):
    text = clean_text(value)
    if not text:
        return None
    numbers = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", text)]
    return min(numbers) if numbers else None


def parse_salary(salary):
    text = clean_text(salary)
    if not text or text.lower() in {"locked", "negotiable", "not specified"}:
        return None, None
    numbers = [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]*", text)]
    if not numbers:
        return None, None
    return min(numbers), max(numbers)



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
    job["education_level"] = clean_education(job.get("education"))
    job["experience_years_min"] = parse_experience_years(job.get("experience"))
    job["salary_min_mmk"], job["salary_max_mmk"] = parse_salary(job.get("salary"))
    job["title_normalized"] = re.sub(r"[^a-z0-9 ]", "", (job.get("title") or "").lower()).strip()
    job["processed_at"] = datetime.now(timezone.utc)

    return job
