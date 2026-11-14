# Read-only discovery of standard Salesforce list views for the service Home page.
# Windows PowerShell 5.1 compatible; keep script output ASCII-only.
$ErrorActionPreference = 'Stop'
if (-not (Get-Command sf -ErrorAction SilentlyContinue)) { throw 'Salesforce CLI not found.' }
$objects = @('Account', 'Lead', 'Task', 'Case')
foreach ($objectName in $objects) {
    Write-Host "=== $objectName list views ==="
    $query = "SELECT Id, Name, DeveloperName, SobjectType FROM ListView WHERE SobjectType = '$objectName' ORDER BY Name"
    & sf data query --query $query --target-org SalesforceDev
    if ($LASTEXITCODE -ne 0) { throw "List view discovery failed for $objectName" }
}
Write-Host 'Discovery only. No metadata or data changed.'
