import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "myanmar_job_market")
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY_SECONDS", "3"))
USER_AGENT = os.getenv(
    "SCRAPER_USER_AGENT",
    "MyanmarJobMarketResearch/1.0 (educational project; contact site owner before collection)",
)
MAX_LISTING_PAGES = int(os.getenv("MAX_LISTING_PAGES", "200"))
REFRESH_AFTER_HOURS = int(os.getenv("REFRESH_AFTER_HOURS", "24"))
INACTIVE_AFTER_DAYS = int(os.getenv("INACTIVE_AFTER_DAYS", "3"))
SYNC_INTERVAL_MINUTES = int(os.getenv("SYNC_INTERVAL_MINUTES", "180"))
