# Project Overview

## When to use this

Use this file when you need a concise, evidence-supported understanding of what the repository does before planning or editing.

## What This Project Is

`hwp-to-pdf-api` is a document conversion API prototype. The README describes it as a FastAPI-based service for converting HWP-family files to PDF on Windows using Hancom Office automation through `pywin32`.

Supported input extensions are documented as:

- `.hwp`
- `.hwpx`
- `.hwt`
- `.hwtx`

## Evidence in the Repository

- `app.py` defines the FastAPI application, upload endpoints, health and stats endpoints, local input/output/log directories, and subprocess execution of `convert_hwp.py`.
- `convert_hwp.py` uses Windows COM automation through `win32com.client` and registers `scripts/FilePathCheckerModule.dll` under the current user's Hancom automation registry path.
- `requirements.txt` pins Python dependencies including FastAPI, Uvicorn, Python multipart support, Pydantic, and `pywin32`.
- `README.md` documents Windows Server 2022 or later, Python 3.12 or later, and Hancom Office 2024 as requirements.
- `PUBLIC_PROFILE_AUDIT.md` documents prior public-readiness cleanup and known positioning risks.

## Architecture Summary

The app receives document uploads through FastAPI, writes input files under a local `input` directory, invokes `convert_hwp.py` in a subprocess, and serves generated PDFs from a local `output` directory.

The conversion path depends on Windows-only Hancom Office automation. Agents should not assume cross-platform runtime behavior.

## Boundaries

- This is not documented as a hosted public conversion service.
- No CI configuration, Dockerfile, package manager lockfile, or deployment config is present in the repository evidence.
- Do not infer production infrastructure from examples, local commands, or comments.
- Product source changes are separate product work and should not be mixed into harness or documentation tasks.
