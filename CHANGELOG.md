# Changelog

All notable changes to the **ActionLoop** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-01

### Added
- **Pure LLM Task Extraction**:
  - Implemented extraction pipeline powered by Google Gemini Flash (`gemini-flash-latest` / `gemini-2.5-flash` / `gemini-3.5-flash`) using strict JSON Schemas (`responseSchema`).
  - Verbatim `supporting_quote` requirement to completely eliminate hallucinations.
  - Distinguishes concrete commitments (*"I will deploy the fix by Wednesday"*) from passive discussions (*"we should think about this later"*).
- **Resolver Engine**:
  - Resolves spoken names (*"Priya"*, *"Alex"*) against active workspace member directories.
  - Ambiguity detection: automatically flags ambiguous first-name collisions without guessing.
  - Timezone-aware date resolution converting relative phrases (*"by Friday"*, *"tomorrow EOD"*) into absolute ISO dates.
- **Deduplication Engine**:
  - Jaccard token overlap combined with contrast penalties against existing open tickets in the target project tool.
- **Interactive Review Screen (Next.js 14)**:
  - 30-second review dashboard with inline edit, approve, and reject controls.
  - Side-by-side transcript inspection drawer with highlighted source quotes.
  - Bulk action: "Approve All High-Confidence (>80%)".
  - Duplicate detection warning banners with similarity score indicators.
- **Integrations**:
  - Linear GraphQL API integration with support for custom team routing.
  - Mock sandbox provider for zero-key local testing.
  - Idempotent push: database unique constraint `(workspace_id, task_id)` and lookup-before-retry pattern.
- **SaaS Security & Multi-Tenancy**:
  - Strict tenant scoping via `workspace_id` across all database operations with 404 security enforcement.
  - Token encryption at rest using AES-128-CBC + HMAC-SHA256 (`MultiFernet`) supporting zero-downtime key rotation.
  - Automated transcript retention scheduler purging expired meeting transcripts.
- **Accountability Briefing ("Closing the Loop")**:
  - Pre-meeting recap module summarizing open, completed, and slipped tasks per team member before subsequent meetings.
- **Testing & Benchmarking**:
  - 15 unit, failure-mode, and cross-tenant isolation tests with pytest.
  - 40-case golden evaluation benchmark testing precision, recall, and rejection of negative phrases.

---

## [Unreleased]

### Planned
- Jira, Asana, and GitHub Issues integration adapters.
- Real-time bot integrations for Zoom, Google Meet, and Microsoft Teams.
- Slack & email daily digests for upcoming due dates.

