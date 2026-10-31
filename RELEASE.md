# Release v1.0.0: ActionLoop Initial Release

## 🚀 Overview
**ActionLoop v1.0.0** is the first release of the mini-SaaS platform that transforms unstructured meeting notes and transcripts into deduplicated, owner-resolved tasks in Linear & Jira with an interactive 30-second human review.

---

## 🎯 Highlights & Features

### 1. Pure Model Extraction (Zero Heuristic Fallback)
- **Strict Structured Outputs**: Extracts tasks using Google's Gemini Flash model configured with explicit Pydantic JSON schemas (`EXTRACTION_SCHEMA`).
- **Verbatim Quote Grounding**: Every candidate task requires an exact supporting quote from the transcript.
- **Discussion Filter**: Passive observations and future wishes (e.g., *"we should think about onboarding next quarter"*) are automatically rejected.

### 2. Resolution & Deduplication Engine
- **Workspace Member Resolution**: Spoken names (*"Priya"*, *"Alex"*) are resolved to verified user IDs.
- **Ambiguity Guardrail**: Collisions between attendees with the same first name are explicitly flagged as ambiguous rather than incorrectly assigned.
- **Calendar & Timezone Anchoring**: Temporal terms (*"by Wednesday EOD"*, *"tomorrow morning"*) are converted to absolute ISO dates.
- **Contrast Penalty Deduplication**: Open backlog issues are matched using Jaccard token similarity with contrast penalties to prevent false positives and duplicate tickets.

### 3. SaaS Security & Multi-Tenancy
- **Tenant Isolation**: Strict `workspace_id` scoping across all DB queries with 404 enforcement on unauthorized access.
- **Fernet Token Encryption**: Sensitive OAuth access/refresh tokens are encrypted using AES-128-CBC + HMAC-SHA256 (`MultiFernet`), with support for zero-downtime key rotation.
- **Deep Idempotency**: Database unique constraint `(workspace_id, task_id)` paired with a lookup-before-retry pattern against external PM APIs.
- **GDPR / Transcript Retention**: Automated daily scheduler purges raw transcripts after a configurable retention window (default 30 days).

### 4. Interactive 30-Second Human Review UI
- Built with **Next.js 14**, React, Tailwind CSS, and Lucide Icons.
- Side-by-side transcript inspection drawer with highlighted source quotes.
- One-click "Approve All High-Confidence (>80%)" button.
- Duplicate warning banners with confidence scores.
- Pre-meeting accountability briefings ("Closing the loop") surfacing slipped and open tasks per person.

---

## 🧪 Testing & Verification
- **15 Automated Pytest Suites**: Full coverage for pipeline orchestration, resolution, deduplication, key rotation, deep idempotency, and cross-tenant security.
- **40 Golden Transcripts Benchmark**: Real-world evaluation suite testing precision, recall, and rejection of negative discussion phrases.
