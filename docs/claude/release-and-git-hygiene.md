# Release and Git Hygiene

## When to use this

Use this file before committing, pushing, preparing release notes, or changing repository visibility.

## Git Discipline

- Run `git status --short` before editing and before staging.
- Review `git diff` before staging.
- Stage only files that belong to the task.
- Do not commit `.codex_task.md`, local prompts, environment files, generated input/output documents, logs, or virtual environments.
- Do not include product source changes in documentation-only commits.
- Do not include public-release cleanup work in unrelated tasks.

## Pre-Commit Checks

For documentation-only changes, run:

```powershell
git diff --check
git diff --name-only
```

Verify that changed files are in the allowed scope for the task before committing.

For product changes, add source-appropriate validation and clearly state any environment limitations.

## Push and Release Boundaries

- Confirm the branch name and commit hash after committing.
- Push only the intended branch.
- Do not change repository visibility as part of normal release or documentation work.
- Do not expose production endpoints, internal deployment details, customer data, uploaded documents, or conversion outputs in release notes or PR descriptions.
