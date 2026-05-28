---
title: Agent Harness Docs Need Scope and Validation Guardrails
date: 2026-05-28
category: documentation-gaps
module: agent-harness-docs
problem_type: documentation_gap
component: documentation
severity: low
applies_when:
  - Bootstrapping agent instructions in a private or portfolio-sensitive repository
  - Creating new documentation files that are initially untracked by Git
  - Validating documentation-only work under a strict allowed-file scope
tags: [agent-harness, documentation, scope-validation, privacy, git]
---

# Agent Harness Docs Need Scope and Validation Guardrails

## Context

The task required bootstrapping `AGENTS.md`, `CLAUDE.md`, and shared `docs/claude/` guidance for a private, portfolio-sensitive document conversion API without changing product behavior. The work also required preserving privacy boundaries, proving that only allowed files changed, and capturing the reusable lesson afterward.

## Guidance

For documentation-only harness work in sensitive repositories, start by inspecting current repository evidence and write instructions only from that evidence. Keep root routers concise and put durable guidance in shared docs.

Validate new documentation files explicitly. `git diff --name-only` does not list brand-new untracked files, so use `git status --short` first and, when a full diff is needed before staging content, use intent-to-add:

```powershell
git add -N <new-doc-files>
git diff --check
git diff --name-only
git diff --color=never
```

Stage only the allowed files after the diff review. For privacy-sensitive repos, include explicit non-exposure rules for uploaded documents, conversion outputs, credentials, production endpoints, customer documents, and internal deployment details.

## Mistakes and Failed Attempts

- `git diff --name-only` initially returned no files because all documentation files were untracked.
- A few sandboxed filesystem helper checks failed while trying to validate links with PowerShell and Node-based helpers.
- The practical recovery was to use Git's intent-to-add flow for diff validation and `rg --files` plus diff review to confirm the expected documentation paths existed.

## Review Findings

- The reviewed diff stayed within the allowed harness documentation paths.
- No product source code, dependency files, deployment files, README, or local task file was included.
- The first documentation pass created `docs/solutions/` but root routers did not yet surface that knowledge store, so a small discoverability line was needed.

## Final Solution

- Added concise `AGENTS.md` and `CLAUDE.md` routers.
- Added shared `docs/claude/` guidance covering project overview, repository map, workflow, validation, security, portfolio-showcase rules, and git hygiene.
- Added explicit privacy and portfolio extraction boundaries.
- Added this reusable documentation-gap lesson under `docs/solutions/documentation-gaps/`.
- Added router discoverability for `docs/solutions/`.

## Prevention Rules

- For new documentation files, do not trust `git diff --name-only` until untracked files are represented in the index with `git add -N` or staged intentionally.
- In sensitive repos, document non-exposure rules in both the router and shared source of truth.
- Keep public showcase extraction separate from the original private repository.
- After creating `docs/solutions/`, make sure root instruction files mention the knowledge store so future agents can discover it.

## Related

- `AGENTS.md`
- `CLAUDE.md`
- `docs/claude/README.md`
