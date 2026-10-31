from fastapi import APIRouter
from typing import List, Dict
from services.integrations.mock_provider import MockLinearProvider
from database import get_connection, seed_workspace_if_empty

router = APIRouter(prefix="/api/workspace", tags=["workspace"])

@router.get("/members")
def get_members() -> List[Dict]:
    provider = MockLinearProvider()
    return provider.get_members()

@router.get("/tickets")
def get_open_tickets() -> List[Dict]:
    provider = MockLinearProvider()
    return provider.get_open_tickets()

@router.post("/reset")
def reset_workspace():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM existing_tickets")
    cursor.execute("DELETE FROM workspace_users")
    conn.commit()
    seed_workspace_if_empty(conn)
    conn.close()
    return {"status": "reset_successful"}

