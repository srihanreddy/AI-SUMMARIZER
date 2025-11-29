# PDF SUMMARIZER AI/config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file at the very beginning
load_dotenv()

# API settings
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
API_KEY = os.getenv("GROQ_API_KEY", "")

# This check will now work correctly
if not API_KEY:
    raise ValueError("❌ Missing GROQ_API_KEY. Please set it in your .env file.")

# Retry mechanism settings
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Output settings
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)