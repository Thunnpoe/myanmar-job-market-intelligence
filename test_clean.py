from src.pipeline.clean import clean_job


job = {
    "title": "Data Engineer",
    "company": "CB Bank",
    "location": "Botahtaung | Yangon",
    "job_type": "Full Time",
    "experience": "Experienced Non-Manager"
}


result = clean_job(job)


print(result)