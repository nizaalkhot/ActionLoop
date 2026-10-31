import threading
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import meetings, tasks, workspace, eval, auth, recap
from services.job_runner import BackgroundJobRunner
from services.retention import TranscriptRetentionService

def start_retention_scheduler():
    def scheduler_loop():
        while True:
            # Sleep 24 hours between purge checks (86400 seconds)
            time.sleep(86400)
            try:
                TranscriptRetentionService.purge_expired_transcripts()
            except Exception as e:
                print(f"[RetentionScheduler Error] {e}")

    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    init_db()
    BackgroundJobRunner.recover_interrupted_jobs()
    start_retention_scheduler()
    yield
    # Shutdown tasks (if any)

tags_metadata = [
    {"name": "meetings", "description": "Ingest and process meeting transcripts."},
    {"name": "tasks", "description": "Review, edit, approve, reject, and idempotently push candidate tasks."},
    {"name": "auth", "description": "Linear OAuth 2.0 multi-tenant authorization and encrypted token management."},
    {"name": "recap", "description": "Pre-meeting accountability briefings, surfacing open and slipped tasks per owner."},
    {"name": "evaluation", "description": "Golden benchmark suite evaluating LLM extraction accuracy across 40 real-world scenarios."},
    {"name": "workspace", "description": "Workspace member roster and directory management."},
]

app = FastAPI(
    title="ActionLoop API",
    summary="Turn messy meeting transcripts into deduplicated, owner-resolved tasks.",
    description="Production-grade 6-stage pipeline powered by Gemini Flash structured outputs, multi-tenant isolation, Fernet token encryption, and pre-meeting accountability briefings.",
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(meetings.router)
app.include_router(tasks.router)
app.include_router(workspace.router)
app.include_router(eval.router)
app.include_router(auth.router)
app.include_router(recap.router)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "actionloop-api", "version": "1.2.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
