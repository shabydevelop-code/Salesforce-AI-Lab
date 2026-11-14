# Validate isolated custom Lightning Service Workspace app.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
Set-Location $root
$app = 'Packages/ServiceWorkspace/force-app/main/default/applications/Service_Workspace.app-meta.xml'
$page = 'Packages/ServiceWorkspace/force-app/main/default/flexipages/Service_Representative_Home.flexipage-meta.xml'
if (-not (Get-Command sf -ErrorAction SilentlyContinue)) { throw 'Salesforce CLI not found.' }
if (-not (Test-Path -LiteralPath $app)) { throw "Missing app metadata: $app" }
if (-not (Test-Path -LiteralPath $page)) { throw "Missing Home metadata: $page" }
$old = 'Packages/ServiceWorkspace/force-app/main/default/applications/standard__Service.app-meta.xml'
if (Test-Path -LiteralPath $old) {
    Write-Warning "Unsupported standard app override exists locally: $old"
    throw 'Remove the generated standard__Service.app-meta.xml file before continuing. Do not deploy it.'
}
& sf project deploy validate --source-dir $app --source-dir $page --target-org SalesforceDev --test-level RunLocalTests --wait 10
if ($LASTEXITCODE -ne 0) { throw 'Validation failed. Nothing was deployed.' }
Write-Host 'Custom Lightning app and Home page validated together. Nothing was deployed.'
