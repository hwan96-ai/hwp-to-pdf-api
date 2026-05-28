# Agent Instructions

This file routes Codex and other coding agents to the shared project guidance in `docs/claude/`.

## Start Here

- Read [docs/claude/README.md](docs/claude/README.md) before changing files.
- Use [docs/claude/project-overview.md](docs/claude/project-overview.md) to understand the app and evidence-supported constraints.
- Use [docs/claude/repository-map.md](docs/claude/repository-map.md) before editing or adding files.
- Use [docs/claude/development-workflow.md](docs/claude/development-workflow.md) for local setup and change workflow.
- Use [docs/claude/testing-and-validation.md](docs/claude/testing-and-validation.md) before claiming a change is verified.
- Use [docs/claude/security-and-secrets.md](docs/claude/security-and-secrets.md) for privacy, sensitive files, logs, and endpoint handling.
- Use [docs/claude/portfolio-showcase-rules.md](docs/claude/portfolio-showcase-rules.md) before any public portfolio or showcase discussion.
- Use [docs/claude/release-and-git-hygiene.md](docs/claude/release-and-git-hygiene.md) before commits, pushes, or release-like work.
- `docs/solutions/` contains documented solutions and workflow lessons organized by category with YAML frontmatter; it is relevant when implementing or debugging in documented areas.

## Non-Negotiables

- Treat uploaded documents, generated conversion outputs, file contents, credentials, production endpoints, customer documents, and internal deployment details as sensitive.
- Do not expose sensitive data in prompts, logs, commits, examples, screenshots, or public-facing docs.
- Do not change product behavior unless the user explicitly asks for product work.
- Future public portfolio or showcase extraction must happen in a separate sanitized repository. Do not make this original repository public as the showcase artifact.
- Do not commit local task files such as `.codex_task.md`.
