# Known Technical Errors and Prevention Rules

This file records reusable technical failure patterns, their evidence, and verified prevention practices. It is **not** a project progress log or task tracker. Do not mark a fix as verified until it passes the relevant command.

## SF-FLEXIPAGE-001 — Invalid property `value` in `flexipage:richText`

- **Context:** Salesforce API 65.0 FlexiPage `Service_Representative_Home` in `Packages/ServiceWorkspace/force-app/main/default/flexipages/`.
- **Observed error:** `Invalid property [value] in component [flexipage:richText]`.
- **Evidence:** Salesforce deployment `0Afaj00000rb8rJCAQ` failed with `Components: 0/1`; no successful deployment was reported.
- **Trigger:** A change added `flexipage:richText` component instances with a `componentInstanceProperties` entry named `value` to provide section headings.
- **Cause:** The deployed component configuration does not accept the `value` property. Salesforce's official Metadata API guide shows the supported property name is `richTextValue` (not `value`) for `flexipage:richText`. Reference: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/api_meta.pdf
- **Prevention:** Before introducing a standard Lightning component or property in FlexiPage XML, inspect a working retrieved FlexiPage example or authoritative metadata documentation for the target API version. Validate deployment before treating the change as successful. Do not assume UI component attributes are valid FlexiPage metadata properties.
- **Resolution status:** **Source corrected; deployment unverified**. Commit `7b2d335` replaces three incorrect `value` property names with `richTextValue`. Await successful validation/deployment before marking resolved.

## General rules

- Record the exact error, triggering change, confirmed cause versus hypothesis, and a reusable prevention rule.
- Keep unverified remedies explicitly marked unverified.
- Prefer validation before deploying newly introduced metadata component types or properties.
- Keep troubleshooting knowledge separate from current project state and implementation plans.
