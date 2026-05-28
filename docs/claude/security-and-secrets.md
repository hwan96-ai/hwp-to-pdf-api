# Security and Secrets

## When to use this

Use this file before handling documents, logs, endpoints, examples, credentials, or any potentially sensitive data.

## Sensitive Data

Agents must not expose:

- Uploaded documents
- Conversion outputs
- File contents from user or customer documents
- Credentials, tokens, keys, cookies, or secrets
- Production endpoints
- Customer documents
- Internal deployment details
- Runtime logs that include sensitive filenames, paths, or operational details

This restriction applies to prompts, summaries, commits, generated docs, screenshots, examples, issue text, PR text, and public portfolio material.

## Runtime Data

`app.py` uses local `input`, `output`, and `logs` directories. Treat all files in those locations as sensitive runtime artifacts. Do not commit them or quote their contents.

## Examples and Documentation

- Prefer localhost examples over private network addresses.
- Use placeholders for environment-specific paths.
- Do not include real customer names, filenames, document excerpts, network hosts, or deployment details.
- Do not document a production endpoint unless the user explicitly provides one for that purpose and confirms it is safe to share.

## Dependency and Platform Notes

The app relies on Windows COM automation and Hancom Office. Avoid changing security-related behavior, CORS, file size limits, file storage behavior, or download behavior unless explicitly scoped and reviewed.
