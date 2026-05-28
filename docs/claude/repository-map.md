# Repository Map

## When to use this

Use this file before editing so you can distinguish product code, support assets, public-facing documentation, and agent harness documentation.

## Top-Level Files

- `app.py`: FastAPI application, API endpoints, local file handling, health/stat responses, and Uvicorn entry point.
- `convert_hwp.py`: Windows/Hancom Office automation script used by `app.py` for PDF conversion.
- `requirements.txt`: Python dependency pins.
- `README.md`: Human-facing setup, run, API, limitations, and positioning notes.
- `PUBLIC_PROFILE_AUDIT.md`: Existing public-profile audit and documentation cleanup notes.
- `scripts/FilePathCheckerModule.dll`: Hancom automation support DLL referenced by `convert_hwp.py`.
- `AGENTS.md`: Codex/general-agent router.
- `CLAUDE.md`: Claude Code router.
- `docs/claude/`: Shared durable agent instructions.

## Generated or Sensitive Runtime Paths

`app.py` creates local `input`, `output`, and `logs` directories at runtime. Treat their contents as sensitive. Do not commit uploaded documents, generated PDFs, or logs.

## Editing Boundaries

- Harness documentation belongs in `AGENTS.md`, `CLAUDE.md`, and `docs/claude/`.
- Product behavior lives primarily in `app.py` and `convert_hwp.py`.
- Dependency changes belong in `requirements.txt` and require explicit product/dependency scope.
- Do not add public-release cleanup files or sanitized showcase artifacts to this original repository unless explicitly requested and scoped.
