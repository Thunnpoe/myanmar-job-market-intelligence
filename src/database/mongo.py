from pymongo import MongoClient
from config.settings import MONGODB_URI, DATABASE_NAME

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]

jobs_collection = db["jobs"]

processed_jobs_collection = db["processed_jobs"]