# Testing and Validation

## When to use this

Use this file before claiming a change is complete or verified.

## Repository Evidence

No dedicated test directory, test runner configuration, CI workflow, Dockerfile, or lockfile is present in the current repository evidence.

## Lightweight Documentation Validation

For documentation-only work, run:

```powershell
git diff --check
git diff --name-only
```

Then verify changed files are within the intended scope and review the diff before staging.

## Python Validation Options

When Python source behavior changes are explicitly in scope, use the strongest available local checks. At minimum, consider:

```powershell
python -m py_compile app.py convert_hwp.py
```

Importing or running the full service may require Windows-specific COM and Hancom Office dependencies. Do not claim end-to-end conversion was verified unless an actual supported Windows/Hancom environment was used.

## Manual Runtime Checks

If the app is run locally, the README documents:

- API docs: `http://127.0.0.1:9000/docs`
- Health endpoint: `GET /health`
- Single conversion: `POST /convert`
- Batch conversion: `POST /convert-batch`
- PDF download: `GET /download/{filename}`

Do not use sensitive customer documents or private production files for manual tests.

## Verification Discipline

- State exactly which checks ran.
- State skipped checks and why.
- Do not treat markdown lint, diff review, or import checks as proof of real document conversion.
- Do not expose uploaded documents, outputs, or file contents while reporting test results.
