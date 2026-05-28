# Shared Agent Guidance

## When to use this

Use this file at the start of any agent session in this repository. It is the index for durable instructions shared by Codex, Claude Code, and other coding agents.

## Repository Purpose

This repository contains a FastAPI prototype for converting HWP-family documents to PDF on Windows by automating Hancom Office through `pywin32`.

The repository is private, restricted, or portfolio-sensitive. Treat user documents, generated conversion outputs, logs, endpoints, and deployment details as sensitive.

## Instruction Structure

- [project-overview.md](project-overview.md): Evidence-supported project summary and constraints.
- [repository-map.md](repository-map.md): File layout and ownership boundaries.
- [development-workflow.md](development-workflow.md): Setup, change workflow, and safe editing expectations.
- [testing-and-validation.md](testing-and-validation.md): Verification commands and limits.
- [security-and-secrets.md](security-and-secrets.md): Sensitive-data rules.
- [portfolio-showcase-rules.md](portfolio-showcase-rules.md): Public showcase boundaries.
- [release-and-git-hygiene.md](release-and-git-hygiene.md): Git and release discipline.

## Global Rules

- Infer instructions from repository evidence only. Do not invent deployment topology, customers, production URLs, CI, hosting, or test suites.
- Do not expose uploaded documents, conversion outputs, file contents, credentials, production endpoints, customer documents, or internal deployment details.
- Keep product behavior unchanged unless the user explicitly asks for product changes.
- Do not commit `.codex_task.md`, local prompt files, generated sensitive files, uploaded documents, conversion outputs, or environment files.
- Keep routers such as `AGENTS.md` and `CLAUDE.md` short. Put durable instruction bodies in this directory.
