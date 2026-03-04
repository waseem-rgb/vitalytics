"""Application configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(DATA_DIR / "chroma_db"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vitalytics.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
HARRISON_PDF_PATH = os.getenv(
    "HARRISON_PDF_PATH",
    "/Users/waseemafsar/Desktop/clinical_book/Harrison's Medicine 22nd Ed.pdf",
)

API_V1_PREFIX = "/api/v1"
