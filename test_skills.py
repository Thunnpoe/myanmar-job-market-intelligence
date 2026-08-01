from src.pipeline.extract_skills import extract_skills


job = {
    "title": "Data Engineer",
    "description": """
    Develop ETL pipelines using Python,
    SQL and Azure Data Factory.
    Need communication skills.
    """
}


skills = extract_skills(job)

print(skills)