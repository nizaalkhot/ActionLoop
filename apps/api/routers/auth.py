import os
import uuid
import requests
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import RedirectResponse
from services.crypto import encrypt_token, decrypt_token
from database import get_connection

router = APIRouter(prefix="/api/auth/linear", tags=["auth"])

LINEAR_AUTH_URL = "https://linear.app/oauth/authorize"
LINEAR_TOKEN_URL = "https://api.linear.app/oauth/token"
CLIENT_ID = os.getenv("LINEAR_CLIENT_ID", "mock_linear_client_id")
CLIENT_SECRET = os.getenv("LINEAR_CLIENT_SECRET", "mock_linear_client_secret")
REDIRECT_URI = os.getenv("LINEAR_REDIRECT_URI", "http://localhost:8000/api/auth/linear/callback")

@router.get("/authorize")
def authorize(workspace_id: str = "ws_default"):
    """
    Initiates Linear OAuth 2.0 flow with state parameter containing workspace_id.
    """
    state = f"{workspace_id}:{uuid.uuid4().hex[:12]}"
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "read,write,issues:create",
        "state": state
    }
    query_str = "&".join(f"{k}={v}" for k, v in params.items())
    auth_url = f"{LINEAR_AUTH_URL}?{query_str}"
    return {"auth_url": auth_url, "state": state}

@router.get("/callback")
def oauth_callback(code: str = Query(...), state: str = Query(...)):
    """
    OAuth 2.0 callback endpoint. Exchanges authorization code for access token,
    encrypts the token with AES-256, and stores it in the database.
    """
    workspace_id = state.split(":")[0] if ":" in state else "ws_default"

    # In production with live Linear credentials:
    access_token = ""
    refresh_token = ""
    expires_in = 3600

    if CLIENT_ID != "mock_linear_client_id" and CLIENT_SECRET != "mock_linear_client_secret":
        try:
            resp = requests.post(
                LINEAR_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
            resp.raise_for_status()
            token_data = resp.json()
            access_token = token_data.get("access_token", "")
            refresh_token = token_data.get("refresh_token", "")
            expires_in = token_data.get("expires_in", 3600)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Linear token exchange failed: {e}")
    else:
        # Development / Sandbox simulation
        access_token = f"lin_live_{uuid.uuid4().hex}"
        refresh_token = f"lin_ref_{uuid.uuid4().hex}"

    # Encrypt tokens with AES-256 before storing
    enc_access = encrypt_token(access_token)
    enc_refresh = encrypt_token(refresh_token)
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
    now_iso = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    cursor = conn.cursor()
    token_id = f"tok_{uuid.uuid4().hex[:10]}"
    
    # Upsert oauth token for this workspace
    cursor.execute("DELETE FROM oauth_tokens WHERE workspace_id = ? AND provider = 'linear'", (workspace_id,))
    cursor.execute(
        """
        INSERT INTO oauth_tokens (id, workspace_id, provider, encrypted_access_token, encrypted_refresh_token, expires_at, created_at)
        VALUES (?, ?, 'linear', ?, ?, ?, ?)
        """,
        (token_id, workspace_id, enc_access, enc_refresh, expires_at, now_iso)
    )
    conn.commit()
    conn.close()

    return {
        "status": "connected",
        "workspace_id": workspace_id,
        "provider": "linear",
        "encrypted_storage": "AES-256-Fernet",
        "message": "Linear OAuth connected successfully"
    }

@router.get("/status")
def connection_status(workspace_id: str = "ws_default"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, provider, expires_at, created_at FROM oauth_tokens WHERE workspace_id = ? AND provider = 'linear'",
        (workspace_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"connected": False, "workspace_id": workspace_id}

    return {
        "connected": True,
        "workspace_id": workspace_id,
        "provider": "linear",
        "expires_at": row["expires_at"],
        "connected_at": row["created_at"]
    }

