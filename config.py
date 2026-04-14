import os
from dotenv import load_dotenv

load_dotenv()

MODEL_API = os.getenv("MODEL_API", "")
MODEL_ID = os.getenv("MODEL_ID", "")
USER_KEY = os.getenv("USER_KEY", "")

JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY", "")
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY", "")
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
