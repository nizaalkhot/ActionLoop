# ActionLoop: Meeting Notes → Actionable Tasks

> A deterministic 6-stage intelligence pipeline that solves the **"last mile"** of meeting notes: transforming vague, messy transcripts into high-fidelity, deduplicated, owner-resolved tasks and pushing them to project management tools (Linear/Jira) with an interactive 30-second human review.

---

## 🌟 The Core Problem

Extracting action items from transcripts is a commodity (Otter, Fireflies, Fathom). The actual problem teams face is the **last mile**:
- The extracted items are vague and miss context.
- Spoken names aren't mapped to real team members.
- Relative dates (*"by Friday"*) aren't anchored to the meeting date.
- Items duplicate tickets already in progress.
- Nobody trusts the items enough to act without a fast verification workflow.

## 🚀 How ActionLoop Solves It

1. **Deterministic 6-Stage Pipeline**:
   - **Normalize**: Strips VTT/SRT timing noise, cleans speaker turns, establishes participant rosters, and anchors the meeting date & timezone.
   - **Extract**: Distinguishes commitments (*"I will ship the API"*) from passive discussion (*"We should probably think about this sometime"*). Requires an exact verbatim quote for every task to eliminate hallucinations.
   - **Resolve**: Maps spoken names (*"Priya"*, *"Alex"*) to real workspace member IDs and calculates concrete ISO dates from natural expressions (*"by Friday"* -> `2026-11-06`).
   - **Dedupe**: Token-level and semantic similarity matching against active open tickets in the target project tool to prevent duplicates.
   - **30-Second Human Review**: Rapid inline edit, reject, and approve controls with side-by-side transcript inspection.
   - **Idempotent Push & Learn**: Pushes tickets to Linear with backlinks to the source quote, logging user edits and rejections as an active learning signal.

2. **Ground-Truth Evaluation Benchmark**:
   - Built-in golden evaluation suite testing Precision, Recall, Owner Accuracy, and Date Accuracy across real-world meeting scenarios.

---

## 🛠️ Architecture & Tech Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLite/PostgreSQL, Gemini 2.5 Flash / 1.5 Flash structured outputs with deterministic fallback parser.
- **Frontend**: Next.js 14 (App Router), React, Tailwind CSS, Lucide icons.
- **PM Tool Integration**: Linear GraphQL Provider + Mock Sandbox Provider (zero external keys required for local testing).

---

## ⚡ Quick Start

### 1. Start the FastAPI Backend
```bash
cd apps/api
python -m pip install -r requirements.txt
python main.py
```
Backend API will be running at: `http://localhost:8000`  
Interactive Swagger Docs at: `http://localhost:8000/docs`

### 2. Start the Next.js Frontend
```bash
cd apps/web
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 🧪 Running Automated Tests & Benchmark

### Run Backend Unit Tests:
```bash
cd apps/api
python -m pytest tests -v
```

### Run Golden Benchmark Evaluation:
```bash
cd apps/api
python -c "from routers.eval import run_golden_benchmark; from database import init_db; init_db(); import json; print(json.dumps(run_golden_benchmark(), indent=2))"
```
Or click the **"Run Golden Benchmark Suite"** button in the Web UI!

