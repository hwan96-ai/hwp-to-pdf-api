# Claude Code Instructions

This file routes Claude Code to the shared durable instructions in `docs/claude/`.

## Required Reading

1. [docs/claude/README.md](docs/claude/README.md)
2. [docs/claude/project-overview.md](docs/claude/project-overview.md)
3. [docs/claude/repository-map.md](docs/claude/repository-map.md)
4. [docs/claude/development-workflow.md](docs/claude/development-workflow.md)
5. [docs/claude/testing-and-validation.md](docs/claude/testing-and-validation.md)
6. [docs/claude/security-and-secrets.md](docs/claude/security-and-secrets.md)
7. [docs/claude/portfolio-showcase-rules.md](docs/claude/portfolio-showcase-rules.md)
8. [docs/claude/release-and-git-hygiene.md](docs/claude/release-and-git-hygiene.md)

## Claude-Specific Notes

- Keep this router concise. Put durable project guidance in `docs/claude/`.
- `docs/solutions/` contains documented solutions and workflow lessons organized by category with YAML frontmatter; it is relevant when implementing or debugging in documented areas.
- Do not create files under `.claude/`.
- Treat documents, conversion outputs, credentials, endpoints, customer data, and internal deployment details as sensitive.
- Do not commit `.codex_task.md` or other local-only task files.
- Public portfolio/showcase work must be extracted into a separate sanitized repository, not performed by making this original repository public.
