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
