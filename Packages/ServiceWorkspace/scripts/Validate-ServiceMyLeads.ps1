# Validate only; does not deploy or modify Salesforce.
$ErrorActionPreference = 'Stop'
$source = 'Packages/ServiceWorkspace/force-app/main/default/objects/Lead/listViews/Service_My_Leads.listView-meta.xml'
if (-not (Test-Path $source)) { throw "Missing metadata: $source" }
# sf project deploy validate does not support NoTestRun; RunLocalTests is required here.
& sf project deploy validate --source-dir $source --target-org SalesforceDev --test-level RunLocalTests --wait 10
if ($LASTEXITCODE -ne 0) { throw 'My Leads list view validation failed. Do not deploy.' }
Write-Host 'Validation succeeded. No deployment performed.'
