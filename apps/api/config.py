import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel

# Load .env from current directory or project root
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent / ".env")

class Settings(BaseModel):
    app_name: str = "Meeting Notes to Tasks API"
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    linear_api_key: str = os.getenv("LINEAR_API_KEY", "")
    linear_team_id: str = os.getenv("LINEAR_TEAM_ID", "")
    default_timezone: str = "UTC"
    db_path: str = os.path.join(os.path.dirname(__file__), "meeting_tasks.db")

settings = Settings()

