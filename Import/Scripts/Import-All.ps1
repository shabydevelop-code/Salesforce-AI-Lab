# Run the four Salesforce CRM imports in dependency order.
# Usage: .\Import\Scripts\Import-All.ps1 -TargetOrg SalesforceDev -Apply
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$TargetOrg,

    [switch]$Apply,

    [switch]$AllowAccountDuplicates
)

$ErrorActionPreference = 'Stop'

if (-not $Apply) {
    throw 'No imports started. Specify -Apply to import CRM data.'
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$imports = @(
    'import_accounts.py',
    'import_contacts.py',
    'import_leads.py',
    'import_opportunities.py'
)

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Python was not found in PATH.'
}

Push-Location $repoRoot
try {
    foreach ($script in $imports) {
        $scriptPath = Join-Path $PSScriptRoot $script
        if (-not (Test-Path -LiteralPath $scriptPath)) {
            throw "Missing import script: $scriptPath"
        }

        Write-Host "Running $script for org $TargetOrg..."
        if ($script -eq 'import_accounts.py' -and $AllowAccountDuplicates) {
            & python $scriptPath --target-org $TargetOrg --apply --allow-account-duplicates
        }
        else {
            & python $scriptPath --target-org $TargetOrg --apply
        }
        if ($LASTEXITCODE -ne 0) {
            throw "$script failed (exit code $LASTEXITCODE). Remaining imports were not started."
        }
        Write-Host "Completed $script."
    }
    Write-Host 'All four CRM imports completed successfully.'
}
finally {
    Pop-Location
}
