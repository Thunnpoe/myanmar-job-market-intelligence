import json
import asyncio
import re
from collections import Counter
from contextlib import asynccontextmanager, suppress
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles

from src.analysis.metrics import count_by, jobs_dataframe, monthly_trend, collection_trend, skill_counts
from src.database.mongo import jobs_collection, processed_jobs_collection
from src.pipeline.process_data import process_pending_jobs


async def reconciliation_loop():
    while True:
        await asyncio.to_thread(process_pending_jobs)
        await asyncio.sleep(15)


@asynccontextmanager
async def lifespan(_app):
    task = asyncio.create_task(reconciliation_loop())
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


app = FastAPI(title="Myanmar Job Market API", version="1.1.0", lifespan=lifespan)
WEB_DIR = Path(__file__).resolve().parents[2] / "web"


class RecommendationRequest(BaseModel):
    target: str = ""
    skills: list[str] = Field(default_factory=list)
    city: str | None = None
    industry: str | None = None
    limit: int = Field(10, ge=1, le=30)


class SkillGapRequest(BaseModel):
    target: str
    skills: list[str] = Field(default_factory=list)


class ComparisonRequest(BaseModel):
    industries: list[str] = Field(min_length=2, max_length=4)


def records(frame):
    if frame.empty:
        return []
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def exact_case_insensitive(value):
    return re.compile(rf"^{re.escape(value.strip())}$", re.IGNORECASE)


def active_query(source=None, industry=None, city=None):
    query = {"is_active": {"$ne": False}}
    if source:
        query["source"] = exact_case_insensitive(source)
    if industry:
        query["industry"] = exact_case_insensitive(industry)
    if city:
        query["city"] = exact_case_insensitive(city)
    return query


@app.get("/api/health")
def health():
    processed_jobs_collection.database.client.admin.command("ping")
    return {"status": "ok"}


@app.get("/api/filters")
def filters():
    query = {"is_active": {"$ne": False}}
    return {
        "sources": sorted(value for value in processed_jobs_collection.distinct("source", query) if value),
        "industries": sorted(value for value in processed_jobs_collection.distinct("industry", query) if value),
        "cities": sorted(value for value in processed_jobs_collection.distinct("city", query) if value),
    }


@app.get("/api/dashboard")
def dashboard(
    source: str | None = None,
    industry: str | None = None,
    city: str | None = None,
    recent_limit: int = Query(20, ge=5, le=100),
):
    query = active_query(source, industry, city)
    projection = {
        "_id": 0,
        "title": 1,
        "company": 1,
        "industry": 1,
        "city": 1,
        "source": 1,
        "skills": 1,
        "education_level": 1,
        "experience_level": 1,
        "salary_min_mmk": 1,
        "salary_max_mmk": 1,
        "posted_date": 1,
        "scraped_at": 1,
        "last_seen_at": 1,
        "job_type_clean": 1,
        "url": 1,
    }
    frame = jobs_dataframe(processed_jobs_collection.find(query, projection))
    raw_count = jobs_collection.count_documents({"is_active": {"$ne": False}})

    if frame.empty:
        return {
            "metrics": {"jobs": 0, "raw_jobs": raw_count, "companies": 0, "industries": 0, "cities": 0},
            "industries": [], "locations": [], "skills": [], "education": [],
            "experience": [], "trend": [], "sources": [], "salary_bands": [],
            "recent_jobs": [], "last_sync": None,
            "trend_basis": "No dated jobs are available yet",
        }

    salary = pd.to_numeric(frame.get("salary_min_mmk"), errors="coerce").dropna()
    salary_bands = pd.cut(
        salary,
        bins=[0, 300000, 500000, 800000, 1200000, 2000000, float("inf")],
        labels=["≤300k", "300–500k", "500–800k", "800k–1.2m", "1.2–2m", "2m+"],
        include_lowest=True,
    ).value_counts(sort=False)
    salary_frame = salary_bands.rename_axis("band").reset_index(name="jobs")
    salary_frame["band"] = salary_frame["band"].astype(str)

    sync_columns = [column for column in ["last_seen_at", "scraped_at"] if column in frame]
    last_sync = None
    for column in sync_columns:
        values = pd.to_datetime(frame[column], errors="coerce", utc=True).dropna()
        if not values.empty:
            candidate = values.max()
            if last_sync is None or candidate > last_sync:
                last_sync = candidate

    recent = frame.copy()
    sort_column = "posted_date" if "posted_date" in recent and recent["posted_date"].notna().any() else "scraped_at"
    if sort_column in recent:
        recent = recent.sort_values(sort_column, ascending=False, na_position="last")
    recent_columns = [column for column in ["title", "company", "industry", "city", "source", "job_type_clean", "url"] if column in recent]

    posting_trend = monthly_trend(frame)
    trend_basis = "Monthly posting dates"
    if posting_trend.empty:
        posting_trend = collection_trend(frame).rename(columns={"period": "month"})
        trend_basis = "Daily collection activity (posting dates are not available yet)"

    return {
        "metrics": {
            "jobs": int(len(frame)),
            "raw_jobs": int(raw_count),
            "companies": int(frame.get("company", pd.Series(dtype=str)).nunique()),
            "industries": int(frame.get("industry", pd.Series(dtype=str)).nunique()),
            "cities": int(frame.get("city", pd.Series(dtype=str)).nunique()),
            "salary_disclosed": int(len(salary)),
        },
        "industries": records(count_by(frame, "industry", 12)),
        "locations": records(count_by(frame, "city", 12)),
        "skills": records(skill_counts(frame).head(15)),
        "education": records(count_by(frame, "education_level")),
        "experience": records(count_by(frame, "experience_level")),
        "trend": records(posting_trend),
        "trend_basis": trend_basis,
        "sources": records(count_by(frame, "source")),
        "salary_bands": records(salary_frame),
        "recent_jobs": records(recent[recent_columns].head(recent_limit)),
        "last_sync": last_sync.isoformat() if last_sync is not None else None,
    }


def tokens(value):
    return set(re.findall(r"[a-z0-9+#.]+", (value or "").lower()))


def public_job(document, score=None, reasons=None):
    job = {
        "title": document.get("title"), "company": document.get("company"),
        "industry": document.get("industry"), "city": document.get("city"),
        "source": document.get("source"), "job_type": document.get("job_type_clean"),
        "skills": document.get("skills", []), "url": document.get("url"),
    }
    if score is not None:
        job["match_score"] = min(100, round(score))
        job["reasons"] = reasons or []
    return job


@app.get("/api/search")
def smart_search(
    q: str = "", source: str | None = None, industry: str | None = None,
    city: str | None = None, skills: str = "", limit: int = Query(30, ge=5, le=100),
):
    query = active_query(source, industry, city)
    if q.strip():
        pattern = re.compile(re.escape(q.strip()), re.I)
        query["$or"] = [
            {"title": pattern}, {"company": pattern}, {"description": pattern},
            {"skills": pattern}, {"industry": pattern}, {"city": pattern},
            {"education_level": pattern}, {"experience_level": pattern},
            {"job_type_clean": pattern},
        ]
    requested_skills = [exact_case_insensitive(skill) for skill in skills.split(",") if skill.strip()]
    if requested_skills:
        query["skills"] = {"$in": requested_skills}
    documents = processed_jobs_collection.find(query).sort("scraped_at", -1).limit(limit)
    return {"jobs": [public_job(document) for document in documents]}


@app.post("/api/recommendations")
def recommendations(request: RecommendationRequest):
    query = active_query(industry=request.industry, city=request.city)
    documents = processed_jobs_collection.find(query).limit(1500)
    target_tokens = tokens(request.target)
    user_skills = {skill.strip().lower() for skill in request.skills if skill.strip()}
    ranked = []
    for document in documents:
        title_overlap = len(target_tokens & tokens(document.get("title")))
        job_skills = {skill.lower() for skill in document.get("skills", [])}
        skill_overlap = len(user_skills & job_skills)
        score = title_overlap * 22 + skill_overlap * 12
        reasons = []
        if title_overlap:
            reasons.append("Target role match")
        if skill_overlap:
            reasons.append(f"{skill_overlap} matching skill{'s' if skill_overlap != 1 else ''}")
        if request.city and (document.get("city") or "").casefold() == request.city.casefold():
            score += 12; reasons.append("Preferred city")
        if request.industry and (document.get("industry") or "").casefold() == request.industry.casefold():
            score += 12; reasons.append("Preferred industry")
        if not target_tokens and not user_skills:
            score = 25
        ranked.append((score, document, reasons))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return {"recommendations": [public_job(doc, score, reasons) for score, doc, reasons in ranked[:request.limit]]}


@app.post("/api/skill-gap")
def skill_gap(request: SkillGapRequest):
    pattern = re.compile(re.escape(request.target.strip()), re.I)
    query = {"is_active": {"$ne": False}, "$or": [{"title": pattern}, {"industry": pattern}]}
    documents = list(processed_jobs_collection.find(query, {"skills": 1}).limit(1000))
    frequencies = Counter(skill.lower() for document in documents for skill in document.get("skills", []))
    required = [skill for skill, _ in frequencies.most_common(15)]
    current = {skill.strip().lower() for skill in request.skills if skill.strip()}
    missing = [skill for skill in required if skill not in current]
    matched = [skill for skill in required if skill in current]
    coverage = round(len(matched) / len(required) * 100) if required else 0
    return {
        "sample_jobs": len(documents), "coverage": coverage, "matched": matched,
        "missing": missing, "demanded_skills": [{"skill": skill, "jobs": count} for skill, count in frequencies.most_common(15)],
    }


@app.get("/api/demand-predictor")
def demand_predictor(career: str):
    pattern = re.compile(re.escape(career.strip()), re.I)
    role_query = {"is_active": {"$ne": False}, "$or": [{"title": pattern}, {"industry": pattern}]}
    role_jobs = processed_jobs_collection.count_documents(role_query)
    total_jobs = max(1, processed_jobs_collection.count_documents({"is_active": {"$ne": False}}))
    companies = len(processed_jobs_collection.distinct("company", role_query))
    share = role_jobs / total_jobs
    score = min(100, round(share * 500 + min(companies, 50)))
    outlook = "High demand" if score >= 65 else "Steady demand" if score >= 35 else "Niche / emerging"
    return {
        "career": career, "active_jobs": role_jobs, "companies": companies,
        "market_share": round(share * 100, 1), "demand_score": score,
        "outlook": outlook, "confidence": "Current-market estimate",
    }


@app.post("/api/comparison")
def comparison(request: ComparisonRequest):
    results = []
    for industry in request.industries:
        query = active_query(industry=industry)
        documents = list(processed_jobs_collection.find(query, {"company": 1, "skills": 1, "salary_min_mmk": 1}))
        skill_frequency = Counter(skill.casefold() for document in documents for skill in document.get("skills", []) if skill)
        salaries = [document.get("salary_min_mmk") for document in documents if document.get("salary_min_mmk")]
        results.append({
            "industry": industry, "jobs": len(documents),
            "companies": len({document.get("company") for document in documents if document.get("company")}),
            "top_skills": [skill for skill, _ in skill_frequency.most_common(5)],
            "median_salary": int(pd.Series(salaries).median()) if salaries else None,
        })
    return {"comparison": results}


app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
