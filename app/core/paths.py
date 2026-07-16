from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_DIR = PROJECT_ROOT / "data"

DATABASE_DIR = DATA_DIR / "database"
DOCUMENTS_DIR = DATA_DIR / "documents"
CHROMA_DIR = DATA_DIR / "chroma"
CACHE_DIR = DATA_DIR / "cache"
LOG_DIR = DATA_DIR / "logs"
MODELS_DIR = DATA_DIR / "models"

REQUIRED_DIRECTORIES = [
    DATA_DIR,
    DATABASE_DIR,
    DOCUMENTS_DIR,
    CHROMA_DIR,
    CACHE_DIR,
    LOG_DIR,
    MODELS_DIR,
]

for directory in REQUIRED_DIRECTORIES:
    directory.mkdir(parents=True, exist_ok=True)