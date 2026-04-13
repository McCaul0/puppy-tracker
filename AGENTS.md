# puppy_tracker Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-11

## Active Technologies
- Python 3.11+ (current workspace uses Python 3.13.5) + FastAPI 0.116.1, Pydantic 2.11.7, Uvicorn, vanilla browser JavaScript, SQLite-backed local storage (003-tap-to-log-status-tiles)
- Python 3.11+ (current workspace uses Python 3.13.5) + FastAPI 0.116.1, Pydantic 2.11.7, Uvicorn, vanilla browser JavaScript (001-expected-schedule-guidance)
- SQLite via the existing `settings` and `events` tables; no schema change required for the first cut (002-simplify-routine-editing)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.11+ (current workspace uses Python 3.13.5): Follow standard conventions

## Recent Changes
- 002-simplify-routine-editing: Added Python 3.11+ (current workspace uses Python 3.13.5) + FastAPI 0.116.1, Pydantic 2.11.7, Uvicorn, vanilla browser JavaScript
- 003-tap-to-log-status-tiles: Added implementation planning artifacts for tap-to-log status tiles with the existing FastAPI, SQLite, and vanilla JavaScript stack
- 001-expected-schedule-guidance: Added Python 3.11+ (current workspace uses Python 3.13.5) + FastAPI 0.116.1, Pydantic 2.11.7, Uvicorn, vanilla browser JavaScript

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
