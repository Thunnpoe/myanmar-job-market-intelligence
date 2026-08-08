import json
import re
from pathlib import Path


SKILLS_PATH = Path(__file__).resolve().parents[2] / "config" / "skills.json"
with SKILLS_PATH.open("r", encoding="utf-8") as file:
    skills_data = json.load(file)


ALL_SKILLS = (
    skills_data["technical"]
    + skills_data["soft"]
)


def extract_skills(job):

    text = ""

    if job.get("title"):
        text += job["title"] + " "

    if job.get("description"):
        text += job["description"]


    text = text.lower()


    found_skills = []


    for skill in ALL_SKILLS:

        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

        if re.search(pattern, text):

            found_skills.append(skill)


    return found_skills
