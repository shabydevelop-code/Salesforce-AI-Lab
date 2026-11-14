# Salesforce Architecture Principles

## OOTB First — Mandatory Decision Rule

Before writing or modifying Salesforce code, verify whether the requirement can be met using supported native Salesforce capabilities.

Apply the following order:

1. **Out of the Box (OOTB)** — Use existing Salesforce functionality.
2. **Configuration** — Prefer supported settings, permissions, translations, and no-code configuration.
3. **Declarative tools** — Consider Flow, Lightning App Builder, and other supported declarative capabilities.
4. **Custom development** — Use Apex, LWC, or Aura only when the preceding options do not adequately meet the requirement.

### Required checks

- Consult current official Salesforce documentation before concluding that a capability is unavailable.
- Explain why native or declarative alternatives are insufficient before proposing custom code.
- Prefer upgrade-compatible, low-maintenance solutions.
- When custom development is necessary, isolate it as far as practical to support independent deployment, versioning, disabling, and removal.
- Do not build a custom feature solely because it is technically possible.

**Guiding principle:** Configuration over Customization.

### Example: Hebrew user interface

Enabling Hebrew as an available end-user language and selecting it in the user's Language settings allowed Salesforce to display Hebrew UI and right-to-left layout. Checking the supported configuration first avoided unnecessary translation and RTL code.

## CLI First — Mandatory Execution Rule

Prefer Salesforce CLI or supported APIs over manual Salesforce UI actions whenever practical.

- Check CLI, Metadata API, Tooling API, and supported automation options before recommending UI steps.
- Store repeatable scripts and metadata in GitHub on the **main** branch as the source of truth.
- The assistant commits GitHub changes; the user runs `git pull --ff-only origin main` and executes commands locally in PowerShell.
- Validate before deploying when supported. Never claim deployment or activation without a confirmed result.
- Use the Salesforce UI only when automation is impractical or visual inspection is required.
- Keep scripts compatible with Windows PowerShell.
- CLI First complements and does not override OOTB First.

## Hebrew UI Guidance — Mandatory Communication Rule

When guiding the user through Salesforce screens, menus, buttons, settings, or navigation, use the **Hebrew labels displayed in the Salesforce UI** and write the guidance in Hebrew (RTL). Do not default to English menu paths now that the user's Salesforce interface is in Hebrew.

- When a label's exact Hebrew translation is uncertain, explicitly indicate the uncertainty; optionally include the original English label (in parentheses) to help locate it.
- Keep technical identifiers, API names, CLI commands, and source-code symbols in their original language.
- Prefer navigation instructions matching the user's current Salesforce UI over generic English documentation paths.

## Lightning App Deployment and Access — Mandatory Verification

- Deploying a `CustomApplication` does **not** by itself establish that a user's profile can access the app. Verify **User Profiles / Selected Profiles** in the Lightning App Manager or the equivalent supported profile `applicationVisibilities` metadata.
- `AppMenuItem.IsVisible = true` confirms app-menu visibility metadata, **not** effective access for a particular user.
- Verify both app presence and access: open it as the target user and confirm its Home page renders. For an unpackaged custom Lightning app, test the name-based route `/lightning/app/c__<DeveloperName>`; do not assume the `CustomApplication` record ID is a valid route.
- Before changing permissions, distinguish a malformed app URL from an app access failure. Check the actual app's **User Profiles** selection and the route first.
- A Permission Set assignment is not a substitute for verifying the app's effective profile access. Do not create permission sets speculatively.
- Prefer targeted, supported Metadata API changes when automating profile app visibility. A profile retrieval may omit `applicationVisibilities` when relevant metadata was not included in the retrieve; absence in a partial retrieval is not proof of denial. Avoid deploying an entire retrieved profile because it can overwrite unrelated settings.
- When a SOQL query fails with an unknown field or object, inspect the object's supported schema (describe/official API reference) instead of guessing field names. Metadata nested properties are not automatically queryable SOQL columns.
- Keep these checks part of future app deployment verification; do not treat a successful validation/deploy as proof of user accessibility.

This document records stable architecture and collaboration rules, not implementation status or release progress.
