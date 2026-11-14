# Architecture Principles

## Encapsulate recurring operations

When working with Salesforce CLI or other integrations, identify recurring patterns of commands, parameters, validation, error handling, and result parsing. Prefer consolidating proven recurring patterns into small, reusable, clearly named operations rather than repeatedly assembling ad-hoc commands.

- Start incrementally: encapsulate a pattern only after identifying actual repetition and understanding its inputs, outputs, and failure cases.
- Each operation should have a stable interface, explicit parameters, predictable structured output, and consistent error handling.
- Keep implementation details (CLI syntax, authentication checks, paths, and parsing) inside the operation, not scattered across callers.
- Preserve visibility into the underlying command and diagnostic output for troubleshooting.
- Validate the real Salesforce Org state before changes and verify results afterward when relevant.
- Avoid premature frameworks or unnecessary abstraction; reuse existing scripts where practical.
- Treat this as an evolving architectural direction, not a commitment to implement a full MCP server now. In the future, these operations could form the basis of a custom MCP interface.

This document describes a durable engineering principle, not project progress, current implementation status, or a task list.

## Validate changes against authoritative contracts

- Inspect the existing implementation and metadata before editing.
- For unfamiliar Salesforce metadata component properties, CLI flags, or API fields, verify the exact names and supported structure against authoritative documentation or a working retrieved example. Do not infer metadata property names from UI attributes.
- Make the smallest change needed; preserve unrelated behavior.
- Run an appropriate validation or deployment check, inspect the actual error output, and correct the root cause before calling the change complete.
- Distinguish a successful deployment from visual or functional acceptance; verify the relevant behavior separately when needed.
- Turn recurring failure patterns into reusable working rules here rather than maintaining a running log of one-off errors or project progress.

## Salesforce Bulk CSV encoding

- Export CSV files for Salesforce Bulk API as **UTF-8 without BOM**. A UTF-8 BOM at the beginning of the file can be interpreted as part of the first field name (for example, `\uFEFFSubject` rather than `Subject`), causing `InvalidBatch: Field name not found`.
- Before a bulk import, inspect the first header field and verify that it contains no leading U+FEFF character; also validate row count and expected column names.
- For PowerShell file generation, explicitly use a BOM-free UTF-8 encoding (for example, `[System.Text.UTF8Encoding]::new($false)`) rather than assuming the default encoding.
- If an ingest job fails, inspect its result and verify whether any records were inserted before retrying, to avoid duplicates.
