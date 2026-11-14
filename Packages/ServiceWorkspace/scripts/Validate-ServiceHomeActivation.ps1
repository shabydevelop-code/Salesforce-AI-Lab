# Validate Service app Home assignment without activating it.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
Set-Location $root
$file = 'Packages/ServiceWorkspace/force-app/main/default/applications/standard__Service.app-meta.xml'
if (-not (Test-Path -LiteralPath $file)) { throw 'Run Prepare-ServiceHomeActivation.ps1 first.' }
& sf project deploy validate --source-dir $file --target-org SalesforceDev --test-level RunLocalTests --wait 10
if ($LASTEXITCODE -ne 0) { throw 'Validation failed. Nothing was deployed.' }
Write-Host 'Validation succeeded. Nothing was deployed or activated.'
