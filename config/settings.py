import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("MONGODB_DATABASE")
REQUEST_DELAY = int(os.getenv("REQUEST_DELAY_SECONDS", 3))