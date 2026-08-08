from pymongo import MongoClient
from config.settings import MONGODB_URI, DATABASE_NAME

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]

jobs_collection = db["jobs"]

processed_jobs_collection = db["processed_jobs"]

def ensure_indexes():
    """Create indexes once MongoDB is known to be reachable."""
    jobs_collection.create_index([("source", 1), ("url", 1)], unique=True)
    processed_jobs_collection.create_index([("source", 1), ("url", 1)], unique=True)
