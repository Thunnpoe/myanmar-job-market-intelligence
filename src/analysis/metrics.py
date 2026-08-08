import pandas as pd


def jobs_dataframe(documents):
    frame = pd.DataFrame(list(documents))
    if frame.empty:
        return frame
    for column in ["posted_date", "scraped_at", "processed_at"]:
        if column in frame:
            frame[column] = pd.to_datetime(frame[column], errors="coerce", utc=True)
    return frame


def count_by(frame, column, limit=None):
    if frame.empty or column not in frame:
        return pd.DataFrame(columns=[column, "jobs"])
    result = frame[column].fillna("Not specified").value_counts().rename_axis(column).reset_index(name="jobs")
    return result.head(limit) if limit else result


def monthly_trend(frame):
    if frame.empty or "posted_date" not in frame:
        return pd.DataFrame(columns=["month", "jobs"])
    data = frame.dropna(subset=["posted_date"]).copy()
    data["month"] = data["posted_date"].dt.to_period("M").astype(str)
    return data.groupby("month", as_index=False).size().rename(columns={"size": "jobs"})


def collection_trend(frame):
    if frame.empty or "scraped_at" not in frame:
        return pd.DataFrame(columns=["period", "jobs"])
    data = frame.dropna(subset=["scraped_at"]).copy()
    data["period"] = data["scraped_at"].dt.strftime("%Y-%m-%d")
    return data.groupby("period", as_index=False).size().rename(columns={"size": "jobs"})


def skill_counts(frame):
    if frame.empty or "skills" not in frame:
        return pd.DataFrame(columns=["skill", "jobs"])
    exploded = frame[["skills"]].explode("skills").dropna()
    return exploded["skills"].value_counts().rename_axis("skill").reset_index(name="jobs")
