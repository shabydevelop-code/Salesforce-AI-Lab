# IVR Account Redirect

Isolated Salesforce source package for opening an Account by `AccountNumber`.

## URL

`https://YOUR_MY_DOMAIN.lightning.force.com/lightning/cmp/c__IvrAccountRedirect?c__accountNumber=LAB-0001`

The Aura component is URL-addressable; the controller performs a user-mode Account query. The browser user must be authenticated and authorized to access the Account.

## Deploy to a development org

From the repository root:

```powershell
sf project deploy start --source-dir Packages/IVR-AccountRedirect/force-app --target-org SalesforceDev --test-level RunSpecifiedTests --tests IvrAccountLookupControllerTest
```

Assign the permission set to an authorized test user (requires suitable admin privileges):

```powershell
sf org assign permset --name IvrAccountRedirectUser --target-org SalesforceDev
```

## 2GP packaging

This directory is configured as an **unlocked-package candidate** in `sfdx-project.json`. A real package ID, version, and installation link **do not exist yet**. Creating an unlocked package requires a configured Dev Hub, package creation, and package version creation. Do not claim that a source deployment is an installed package.

For distribution to unrelated customer orgs, evaluate managed 2GP packaging and namespace/IP requirements before publication.

## Disable / uninstall

Before 2GP installation, remove the deployed metadata deliberately or disable access. After packaging, use the Salesforce package lifecycle. Package uninstall can have dependencies and side effects; it is not a universal rollback of data.

## Design constraints

No modifications to standard Account metadata. Uses existing `AccountNumber` and checks for zero/multiple matches. Authorization is enforced with `with sharing` and `WITH USER_MODE`. AccountNumber must not be treated as a secret; URLs may appear in browser history and logs.
