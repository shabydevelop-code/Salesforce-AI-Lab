# Validate the isolated Service Workspace Home page without deploying it.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
Set-Location $root
$page = 'Packages/ServiceWorkspace/force-app/main/default/flexipages/Service_Representative_Home.flexipage-meta.xml'
if (-not (Test-Path -LiteralPath $page)) { throw "Missing FlexiPage metadata: $page" }
if (-not (Get-Command sf -ErrorAction SilentlyContinue)) { throw 'Salesforce CLI not found.' }
& sf project deploy validate --source-dir $page --target-org SalesforceDev --test-level RunLocalTests --wait 10
if ($LASTEXITCODE -ne 0) { throw 'FlexiPage validation failed. Nothing was deployed.' }
Write-Host 'Validation succeeded. Nothing was deployed or activated.'
