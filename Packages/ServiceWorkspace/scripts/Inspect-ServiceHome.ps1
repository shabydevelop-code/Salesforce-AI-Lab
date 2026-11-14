# Read-only discovery of existing Salesforce Lightning Home pages and apps.
# Run from the repository root: & ".\Packages\ServiceWorkspace\scripts\Inspect-ServiceHome.ps1"
$ErrorActionPreference = 'Stop'
$org = 'SalesforceDev'
if (-not (Get-Command sf -ErrorAction SilentlyContinue)) { throw 'Salesforce CLI (sf) was not found in PATH.' }

function Get-MetadataMembers([string]$type) {
    $raw = & sf org list metadata --metadata-type $type --target-org $org --json
    if ($LASTEXITCODE -ne 0) { throw "Salesforce metadata listing failed for $type." }
    $response = ($raw -join "`n") | ConvertFrom-Json
    if ($response.status -ne 0) { throw "Salesforce returned an error for $type." }
    return @($response.result)
}

Write-Host '=== Lightning Home page candidates (FlexiPage) ==='
$pages = @(Get-MetadataMembers 'FlexiPage')
$pages | Where-Object {
    $_.fullName -match 'Home|Service|Console' -or $_.fileName -match 'Home|Service|Console'
} | Select-Object fullName, fileName | Format-Table -AutoSize
Write-Host "Total FlexiPages in org: $($pages.Count)"

Write-Host '=== Service application candidates (CustomApplication) ==='
$apps = @(Get-MetadataMembers 'CustomApplication')
$apps | Where-Object {
    $_.fullName -match 'Service|Console|standard__Service'
} | Select-Object fullName, fileName | Format-Table -AutoSize
Write-Host "Total applications in org: $($apps.Count)"
Write-Host 'Read-only inspection complete. No metadata was changed.'
