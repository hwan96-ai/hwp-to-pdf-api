# Portfolio Showcase Rules

## When to use this

Use this file before making public-facing, portfolio, showcase, repository visibility, README positioning, or profile-related changes.

## Core Rule

Future public portfolio or showcase extraction must happen in a separate sanitized repository. Do not make this original repository public as the showcase artifact.

## Why

This repository is private, restricted, or portfolio-sensitive and may contain operational context for a document conversion API. Even if obvious secrets are removed, the original repository can still carry sensitive history, file paths, runtime assumptions, deployment details, or document workflow context.

## Allowed in This Repository

- Internal documentation about safe showcase boundaries.
- Private audit notes about public-readiness risks.
- Sanitized README wording that avoids private endpoints, local machine paths, customer context, and internal deployment details.

## Not Allowed Without Separate Explicit Scope

- Creating a public showcase repository.
- Making this original repository public.
- Adding public-release cleanup artifacts to this repository.
- Publishing screenshots, logs, uploaded documents, conversion outputs, real filenames, production endpoints, or internal deployment details.

## Sanitized Showcase Expectations

A separate showcase repository should use safe sample inputs, mock or generated data, sanitized configuration, and no private runtime artifacts. It should not rely on making this repository public.
