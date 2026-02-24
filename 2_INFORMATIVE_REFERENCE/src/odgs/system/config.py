import os
from pathlib import Path
from dotenv import load_dotenv

# Path Strategy:
# 1. ODGS_PROJECT_ROOT env var (explicit override)
# 2. /app (Docker container convention)
# 3. Walk up from __file__ (local dev: src/odgs/system/config.py -> project_root)
CURRENT_FILE = Path(__file__).resolve()
_file_based_root = CURRENT_FILE.parent.parent.parent.parent.parent

if os.getenv("ODGS_PROJECT_ROOT"):
    PROJECT_ROOT = Path(os.getenv("ODGS_PROJECT_ROOT"))
elif Path("/app/lib").exists():
    PROJECT_ROOT = Path("/app")
else:
    PROJECT_ROOT = _file_based_root

# Load .env file
env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path)

class Settings:
    """
    Centralized Configuration for ODGS.
    """
    # Security
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # AI Factory
    # User requested gemini-3.0-flash-preview
    GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3.0-flash-preview")
    
    # Paths
    PROJECT_ROOT = PROJECT_ROOT
    DATA_DIR = PROJECT_ROOT / "data"
    DRAFTS_DIR = DATA_DIR / "drafts"

settings = Settings()
