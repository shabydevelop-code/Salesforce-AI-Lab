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

This document records stable architecture rules, not implementation status or release progress.
