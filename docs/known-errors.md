# Known Technical Errors and Prevention Rules

This file records reusable technical failure patterns, their evidence, and verified prevention practices. It is **not** a project progress log or task tracker. Do not mark a fix as verified until it passes the relevant command.

## SF-FLEXIPAGE-001 — Invalid property `value` in `flexipage:richText`

- **Context:** Salesforce API 65.0 FlexiPage `Service_Representative_Home` in `Packages/ServiceWorkspace/force-app/main/default/flexipages/`.
- **Observed error:** `Invalid property [value] in component [flexipage:richText]`.
- **Evidence:** Salesforce deployment `0Afaj00000rb8rJCAQ` failed with `Components: 0/1`; no successful deployment was reported.
- **Trigger:** A change added `flexipage:richText` component instances with a `componentInstanceProperties` entry named `value` to provide section headings.
- **Cause:** The deployed component configuration does not accept the `value` property. The correct supported metadata representation has **not yet been established**; do not guess a replacement property.
- **Prevention:** Before introducing a standard Lightning component or property in FlexiPage XML, inspect a working retrieved FlexiPage example or authoritative metadata documentation for the target API version. Validate deployment before treating the change as successful. Do not assume UI component attributes are valid FlexiPage metadata properties.
- **Resolution status:** **Unresolved / unverified**. A corrected page must pass validation/deployment before this entry is updated.

## General rules

- Record the exact error, triggering change, confirmed cause versus hypothesis, and a reusable prevention rule.
- Keep unverified remedies explicitly marked unverified.
- Prefer validation before deploying newly introduced metadata component types or properties.
- Keep troubleshooting knowledge separate from current project state and implementation plans.
