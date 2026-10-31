import sqlite3
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from config import settings

DB_FILE = settings.db_path

def get_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Workspaces for tenant isolation
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workspaces (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # Encrypted OAuth tokens (Fernet: AES-128-CBC + HMAC-SHA256)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS oauth_tokens (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        provider TEXT NOT NULL,
        encrypted_access_token TEXT NOT NULL,
        encrypted_refresh_token TEXT,
        expires_at TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    );
    """)

    # Database-level idempotency table with unique constraint
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS idempotency_keys (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        ticket_id TEXT NOT NULL,
        ticket_url TEXT,
        fingerprint TEXT,
        created_at TEXT NOT NULL,
        UNIQUE(workspace_id, task_id)
    );
    """)
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_idempotency_unique ON idempotency_keys(workspace_id, task_id);")

    # Meetings with retention & privacy controls
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meetings (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL DEFAULT 'ws_default',
        title TEXT NOT NULL,
        meeting_date TEXT NOT NULL,
        timezone TEXT NOT NULL,
        transcript_raw TEXT,
        transcript_clean TEXT,
        detected_speakers TEXT NOT NULL,
        retention_days INTEGER DEFAULT 30,
        purged_at TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    );
    """)

    # Background async jobs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS background_jobs (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL DEFAULT 'ws_default',
        status TEXT NOT NULL, -- queued, running, completed, failed
        stage TEXT NOT NULL,
        progress REAL DEFAULT 0.0,
        result_meeting_id TEXT,
        error_message TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # Task Candidates
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS task_candidates (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL DEFAULT 'ws_default',
        meeting_id TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        raw_owner TEXT,
        resolved_owner_id TEXT,
        resolved_owner_name TEXT,
        owner_confidence REAL DEFAULT 0.0,
        raw_due_date TEXT,
        resolved_due_date TEXT,
        date_confidence REAL DEFAULT 0.0,
        supporting_quote TEXT NOT NULL,
        confidence REAL DEFAULT 0.85,
        task_type TEXT DEFAULT 'feature',
        status TEXT DEFAULT 'pending',
        possible_duplicate_of TEXT,
        duplicate_score REAL DEFAULT 0.0,
        pushed_ticket_id TEXT,
        pushed_ticket_url TEXT,
        task_fingerprint TEXT,
        is_ambiguous INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (meeting_id) REFERENCES meetings(id),
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    );
    """)

    # Feedback logs for tracking edits and rejections
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id TEXT NOT NULL DEFAULT 'ws_default',
        meeting_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        action TEXT NOT NULL,
        original_value TEXT,
        corrected_value TEXT,
        reason TEXT,
        timestamp TEXT NOT NULL
    );
    """)

    # Workspace Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workspace_users (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL DEFAULT 'ws_default',
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        avatar_url TEXT,
        role TEXT,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    );
    """)

    # Existing Tickets for Deduplication
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS existing_tickets (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL DEFAULT 'ws_default',
        title TEXT NOT NULL,
        status TEXT NOT NULL,
        assignee_name TEXT,
        project_id TEXT,
        fingerprint TEXT,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    );
    """)

    # Migrations for existing databases
    def add_col_if_missing(table, col, col_def):
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
        except Exception:
            pass

    add_col_if_missing("meetings", "workspace_id", "TEXT NOT NULL DEFAULT 'ws_default'")
    add_col_if_missing("meetings", "retention_days", "INTEGER DEFAULT 30")
    add_col_if_missing("meetings", "purged_at", "TEXT")
    add_col_if_missing("task_candidates", "workspace_id", "TEXT NOT NULL DEFAULT 'ws_default'")
    add_col_if_missing("task_candidates", "is_ambiguous", "INTEGER DEFAULT 0")
    add_col_if_missing("task_candidates", "task_fingerprint", "TEXT")
    add_col_if_missing("existing_tickets", "workspace_id", "TEXT NOT NULL DEFAULT 'ws_default'")
    add_col_if_missing("existing_tickets", "fingerprint", "TEXT")
    add_col_if_missing("workspace_users", "workspace_id", "TEXT NOT NULL DEFAULT 'ws_default'")

    conn.commit()
    seed_workspace_if_empty(conn)
    conn.close()

def seed_workspace_if_empty(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM workspaces WHERE id = 'ws_default'")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("INSERT INTO workspaces (id, name, created_at) VALUES ('ws_default', 'Acme Engineering', ?)", (datetime.now(timezone.utc).isoformat(),))

    cursor.execute("SELECT COUNT(*) as count FROM workspace_users WHERE workspace_id = 'ws_default'")
    if cursor.fetchone()["count"] == 0:
        sample_users = [
            ("usr_priya", "ws_default", "Priya Sharma", "priya@startup.co", "https://api.dicebear.com/7.x/avataaars/svg?seed=Priya", "Frontend Lead"),
            ("usr_alex_chen", "ws_default", "Alex Chen", "alex.chen@startup.co", "https://api.dicebear.com/7.x/avataaars/svg?seed=AlexChen", "Backend Lead"),
            ("usr_alex_miller", "ws_default", "Alex Miller", "alex.miller@startup.co", "https://api.dicebear.com/7.x/avataaars/svg?seed=AlexMiller", "Growth Engineer"),
            ("usr_marcus", "ws_default", "Marcus Vance", "marcus@startup.co", "https://api.dicebear.com/7.x/avataaars/svg?seed=Marcus", "Product Manager"),
            ("usr_sarah", "ws_default", "Sarah Jenkins", "sarah@startup.co", "https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah", "DevOps / Infra"),
            ("usr_elena", "ws_default", "Elena Rostova", "elena@startup.co", "https://api.dicebear.com/7.x/avataaars/svg?seed=Elena", "Designer")
        ]
        cursor.executemany("INSERT INTO workspace_users (id, workspace_id, name, email, avatar_url, role) VALUES (?, ?, ?, ?, ?, ?)", sample_users)

    cursor.execute("SELECT COUNT(*) as count FROM existing_tickets WHERE workspace_id = 'ws_default'")
    if cursor.fetchone()["count"] == 0:
        sample_tickets = [
            ("LIN-101", "ws_default", "Refactor authentication middleware for JWT refresh tokens", "In Progress", "Alex Chen", "proj_core", "fp_auth_middleware"),
            ("LIN-102", "ws_default", "Fix mobile navigation drawer overlap on iOS Safari", "Backlog", "Priya Sharma", "proj_web", "fp_nav_drawer"),
            ("LIN-103", "ws_default", "Setup GitHub Actions deployment pipeline for staging", "Done", "Sarah Jenkins", "proj_infra", "fp_gh_actions"),
            ("LIN-104", "ws_default", "Redesign project dashboard analytics overview card", "In Review", "Elena Rostova", "proj_design", "fp_dashboard_card"),
            ("LIN-105", "ws_default", "Update pricing page layout and tiers", "Backlog", "Marcus Vance", "proj_web", "fp_pricing_page")
        ]
        cursor.executemany("INSERT INTO existing_tickets (id, workspace_id, title, status, assignee_name, project_id, fingerprint) VALUES (?, ?, ?, ?, ?, ?, ?)", sample_tickets)

    conn.commit()
