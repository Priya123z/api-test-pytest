import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://reqres.in")
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "10"))
