# ActionLoop: Meeting Notes → Actionable Tasks

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Frontend-Next.js%2014-black.svg?logo=next.js)](https://nextjs.org)
[![Gemini](https://img.shields.io/badge/AI%20Engine-Gemini%20Flash%20Structured%20Outputs-4285F4.svg?logo=google)](https://aistudio.google.com)
[![Tests](https://img.shields.io/badge/Tests-15%2F15%20Passing-brightgreen.svg)]()

**The last mile from unstructured meeting notes to deduplicated, owner-resolved tickets in Linear & Jira.**

[Quick Start](#-quick-start) • [Pipeline Architecture](#-pipeline-architecture) • [Evaluation Benchmark](#-evaluation-benchmark) • [GitHub Topics & Tags](#-tags--topics)

</div>

---

## 🌟 The Core Problem

Extracting action items from transcripts is a commodity (Otter, Fireflies, Fathom all do it). The real problem teams actually suffer from is the **last mile**:
- **Hallucinated Tasks**: Models invent tasks from casual banter or brainstorming discussions.
- **Ambiguous Ownership**: Spoken first names (*"Priya"*, *"Alex"*) aren't mapped to verified user IDs in the issue tracker.
- **Floating Due Dates**: Relative dates (*"by Wednesday EOD"*, *"next sprint"*) aren't resolved into concrete calendar dates based on meeting timezones.
- **Duplicate Backlog Sprawl**: The team talks about an ongoing issue and the tool blindly creates a duplicate ticket.
- **Lack of Trust**: Nobody pushes AI output to Linear/Jira without an efficient human-in-the-loop review.
- **No Follow-Through**: Once pushed, tickets are forgotten until someone asks *"whatever happened to that item from two weeks ago?"*

---

## 🚀 How ActionLoop Solves It

ActionLoop treats task extraction as a **mostly deterministic pipeline with structured LLM calls**, not an unpredictable free-roaming agent:

```
[Raw Transcript / Notes]
         │
         ▼
 1. NORMALIZE    ──► Strip VTT/SRT noise, parse speaker labels, anchor meeting date & timezone
         │
         ▼
 2. EXTRACT      ──► Pure Gemini Flash structured output with verbatim quote grounding
         │           (Rejects passive discussion; enforces supporting_quote)
         ▼
 3. RESOLVE      ──► Map spoken names to verified workspace users; compute absolute deadlines
         │           (Flags ambiguous first-name collisions; leaves unassigned if unknown)
         ▼
 4. DEDUPE       ──► Jaccard token overlap + Levenshtein contrast penalties against active backlog
         │
         ▼
 5. REVIEW (UI)  ──► 30-second review screen with side-by-side transcript drawer & quick approve-all
         │
         ▼
 6. PUSH & LEARN ──► Idempotent ticket creation (DB unique constraints + lookup-before-retry)
         │           Logs all human edits/rejections to improve future resolution
         ▼
 7. CLOSE LOOP   ──► Pre-meeting accountability recaps surfacing slipped & open items per owner
```

---

## ✨ Key Features

- **Quote-Grounded Extraction**: Every task candidate requires a verbatim `supporting_quote` directly from the transcript. If the quote doesn't support the commitment, it is rejected.
- **Strict Separation of Discussion vs. Action**: Casual musings (*"We should probably redesign onboarding next quarter"*) are filtered out with zero hallucinated tasks.
- **Ambiguity Guardrails**: Multiple attendees with the same first name (e.g. Alex Chen vs. Alex Rivera) are automatically flagged as `is_ambiguous` rather than guessing wrong.
- **Deep Idempotency**:
  - Database-level unique constraint on `(workspace_id, task_id)`.
  - Lookup-before-retry pattern: if an API call drops mid-batch, subsequent retries query Linear by external backlink before attempting re-creation.
- **Multi-Tenant SaaS Isolation**: All queries enforce strict `workspace_id` tenant scoping. Unauthorized cross-tenant requests yield clean 404 responses.
- **Fernet Token Encryption with Key Rotation**: OAuth tokens are encrypted at rest using AES-128-CBC with HMAC-SHA256 (`MultiFernet`), allowing seamless zero-downtime key rotation.
- **Pre-Meeting Accountability Briefings**: Surfaces open and slipped action items per owner before the next meeting to close the execution loop.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, SQLite / PostgreSQL |
| **Frontend** | Next.js 14 (App Router), React 18, Tailwind CSS, Lucide Icons |
| **AI / LLM** | Google Gemini Flash (Latest / 2.5 / 3.5) with strict JSON Schema (`responseSchema`) |
| **Cryptography**| `cryptography.fernet.MultiFernet` (AES-128-CBC + HMAC-SHA256) |
| **Integrations**| Linear GraphQL API + Mock Sandbox Provider (zero external keys needed for local testing) |

---

## ⚡ Quick Start

### 1. Clone & Setup Environment

```bash
# Clone the repository
git clone https://github.com/nizaalkhot/mini-saas-meeting-notes-into-tasks.git
cd mini-saas-meeting-notes-into-tasks

# Copy environment template
cp .env.example apps/api/.env
```

Open `apps/api/.env` and insert your [Google AI Studio Gemini API Key](https://aistudio.google.com/app/apikey):
```env
GEMINI_API_KEY="your_api_key_here"
```

### 2. Start the FastAPI Backend

```bash
cd apps/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
- Interactive API Documentation: `http://localhost:8000/docs`

### 3. Start the Next.js Frontend

```bash
cd apps/web
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

> [!TIP]
> **Need to run on a different port?**  
> Simply pass `-p <port>`:
> ```bash
> npm run dev -- -p 3001
> ```

---

## 🧪 Automated Testing & Benchmark

### Run the Backend Test Suite
ActionLoop features comprehensive unit, failure-mode, and cross-tenant isolation tests:

```bash
cd apps/api
python -m pytest tests -v
```
All **15/15 tests** pass:
- Direct model extraction with structured schemas
- Cross-tenant multi-tenancy isolation (404 enforcement)
- AES-128-CBC Fernet encryption & zero-downtime key rotation
- Timezone boundary adjustments (e.g. Friday evening *"tomorrow"*)
- Name collision ambiguity resolution
- Deep idempotency (DB constraint + lookup-before-retry)
- Semantic deduplication with contrast penalties

### Run the Evaluation Benchmark
Evaluate precision, recall, and rejection of passive discussion across 40 real-world transcripts:

```bash
# Via CLI
cd apps/api
python -c "from routers.eval import run_golden_benchmark; from database import init_db; init_db(); import json; print(json.dumps(run_golden_benchmark(), indent=2))"
```
Or open the web dashboard at `http://localhost:3000` and click **"Run Model Benchmark"**!

---

## 🏷️ Tags & Topics

When configuring your GitHub repository settings, use the following tags and topics:

`actionloop` • `meeting-notes` • `task-extraction` • `linear-app` • `gemini-api` • `llm` • `structured-outputs` • `fastapi` • `nextjs` • `saas` • `productivity` • `ai-agents` • `fernet-encryption` • `multi-tenant` • `pydantic`

---

## 📦 Release Information

- **Release**: `v1.0.0`
- **Initial Release Date**: November 2026
- **License**: MIT
