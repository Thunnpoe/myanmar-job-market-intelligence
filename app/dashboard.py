import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.analysis.metrics import count_by, jobs_dataframe, monthly_trend, skill_counts
from src.database.mongo import jobs_collection, processed_jobs_collection

st.set_page_config(page_title="Myanmar Job Market", page_icon="🇲🇲", layout="wide")
st.title("Myanmar job market analysis")
st.caption(
    "Public postings from JobNet and MyJobs. Data checks run in the background, "
    "and this dashboard refreshes every 30 seconds."
)


@st.cache_data(ttl="20s", max_entries=2)
def load_market_data():
    frame = jobs_dataframe(processed_jobs_collection.find({}, {"_id": 0}))
    raw_count = jobs_collection.count_documents({})
    return frame, raw_count


try:
    initial_frame, _ = load_market_data()
except Exception as error:
    st.error("MongoDB is unavailable. Start MongoDB or configure MONGODB_URI in .env.")
    st.exception(error)
    st.stop()

with st.sidebar:
    st.header("Filters")
    source = st.multiselect(
        "Source",
        sorted(initial_frame.get("source", pd.Series(dtype=str)).dropna().unique()),
    )
    industry = st.multiselect(
        "Industry",
        sorted(initial_frame.get("industry", pd.Series(dtype=str)).dropna().unique()),
    )
    city = st.multiselect(
        "City",
        sorted(initial_frame.get("city", pd.Series(dtype=str)).dropna().unique()),
    )
    if st.button(":material/refresh: Refresh now", width="stretch"):
        load_market_data.clear()
        st.rerun()


@st.fragment(run_every="30s")
def render_live_dashboard(selected_sources, selected_industries, selected_cities):
    frame, raw_count = load_market_data()

    if frame.empty:
        st.info(
            f"{raw_count:,} raw jobs are collected, but none are processed yet. "
            "Run the processing pipeline."
        )
        return

    if raw_count > len(frame):
        st.warning(
            f"Collection is ahead of analysis: {raw_count:,} raw jobs and "
            f"{len(frame):,} processed jobs."
        )

    filtered = frame.copy()
    if selected_sources:
        filtered = filtered[filtered["source"].isin(selected_sources)]
    if selected_industries and "industry" in filtered:
        filtered = filtered[filtered["industry"].isin(selected_industries)]
    if selected_cities and "city" in filtered:
        filtered = filtered[filtered["city"].isin(selected_cities)]

    with st.container(horizontal=True):
        st.metric("Raw jobs collected", raw_count, border=True)
        st.metric("Jobs analyzed", len(filtered), border=True)
        st.metric(
            "Companies",
            filtered.get("company", pd.Series(dtype=str)).nunique(),
            border=True,
        )
        st.metric(
            "Industries",
            filtered.get("industry", pd.Series(dtype=str)).nunique(),
            border=True,
        )
        st.metric(
            "Cities",
            filtered.get("city", pd.Series(dtype=str)).nunique(),
            border=True,
        )

    left, right = st.columns(2)
    with left:
        st.subheader("Jobs by industry")
        data = count_by(filtered, "industry", 15)
        st.plotly_chart(
            px.bar(data, x="jobs", y="industry", orientation="h"),
            width="stretch",
        )
    with right:
        st.subheader("Jobs by city")
        data = count_by(filtered, "city", 15)
        st.plotly_chart(px.bar(data, x="city", y="jobs"), width="stretch")

    st.subheader("Monthly posting trend")
    trend = monthly_trend(filtered)
    if trend.empty:
        st.info("No valid posted dates in the selected sample.")
    else:
        st.plotly_chart(
            px.line(trend, x="month", y="jobs", markers=True),
            width="stretch",
        )

    st.subheader("Most demanded skills")
    skills = skill_counts(filtered).head(20)
    if skills.empty:
        st.info("Run skill extraction to populate this chart.")
    else:
        st.plotly_chart(
            px.bar(skills, x="jobs", y="skill", orientation="h"),
            width="stretch",
        )

    st.subheader("Experience and education")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            px.pie(
                count_by(filtered, "experience_level"),
                names="experience_level",
                values="jobs",
            ),
            width="stretch",
        )
    with col2:
        st.plotly_chart(
            px.pie(
                count_by(filtered, "education_level"),
                names="education_level",
                values="jobs",
            ),
            width="stretch",
        )


render_live_dashboard(source, industry, city)
