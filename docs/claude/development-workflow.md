# Development Workflow

## When to use this

Use this file when preparing local changes, deciding what files to inspect, or choosing commands for setup and execution.

## Evidence-Based Setup

The README documents this setup flow:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pywin32_postinstall -install
```

Run the app locally as documented:

```powershell
.\venv\Scripts\Activate.ps1
uvicorn app:app --host 127.0.0.1 --port 9000
```

The documented local API docs URL is `http://127.0.0.1:9000/docs`.

## Change Workflow

- Start with `git status --short` and inspect existing changes before editing.
- Read the smallest relevant set of files before changing them.
- Preserve user changes. Do not revert unrelated work.
- Keep documentation-only tasks documentation-only.
- Keep product behavior changes separate from harness, portfolio, or release documentation work.
- Prefer narrow edits over broad rewrites.

## Environment Constraints

The conversion path depends on Windows, Hancom Office, `pywin32`, and local COM automation. If those dependencies are unavailable, document the verification gap instead of pretending conversion was tested.

## Local Files

Do not commit local task files, virtual environments, uploaded input documents, generated PDFs, logs, or environment files.
