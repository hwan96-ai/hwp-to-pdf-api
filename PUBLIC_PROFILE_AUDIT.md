# Public Profile Audit

## Repo

hwp-to-pdf-api

## Repository URL

https://github.com/hwan96-ai/hwp-to-pdf-api

## Current Public Impression

Practical document workflow/API prototype for converting HWP-family files to PDF on Windows with 한컴 오피스 automation.

## Positioning Fit

Medium to high fit. The repo supports AI Technical Consultant / GenAI Pre-Sales / PoC Builder positioning as a document automation and API-oriented PoC example.

## README Quality

Improved. The README now has clearer setup, run, API, example, limitations, and safe environment-specific configuration guidance.

## Technical Signal

Medium. The repository shows a FastAPI service, Python conversion script, dependency file, and HWP automation module support.

## Public Risks

- Original README exposed local machine paths and a private network address.
- The project depends on Windows and installed 한컴 오피스, so portability is limited.
- Manual firewall exposure should be environment-reviewed.

## Sensitive Strings / Naming Risks

Local machine paths and private network examples were replaced with localhost or placeholders. No internal customer naming pattern, placeholder anchor pattern, credential-related pattern, or disallowed positioning phrase was found in markdown scans after cleanup.

## Repository Type

Improve before featuring

## Recommended Action

Improve and commit locally

## Planned Changes

- Rewrite README for public readability.
- Replace local paths and private network examples with safer generic examples.
- Add limitations and positioning sections.
- Add this public profile audit file.

## Changes Intentionally Not Made

- No source code changes.
- No dependency changes.
- No build system changes.
- No repository settings, descriptions, topics, or pinned repositories changed.
- No push or PR.

## Checks Run

- `git status --short`
- `git branch --show-current`
- `git remote -v`
- `git log --oneline --decorate -n 5`
- `git remote show origin`
- `git fetch origin`
- `git pull --ff-only origin main`
- README/docs safety-pattern scan
- Disallowed-positioning scan
- `git diff --stat`
- `git diff`

## Review Findings

- README cleanup was warranted because the repo is a practical document automation API candidate.
- The cleanup stayed documentation-only and did not alter app behavior.
- The repo can be considered for selected work after source-level audit in a later approved phase.

## Lessons to Carry Forward

- Replace local absolute paths and private network examples before featuring API repositories.
- Fix malformed code blocks when cleaning public README files.
- Add limitations for platform-specific automation repos.
