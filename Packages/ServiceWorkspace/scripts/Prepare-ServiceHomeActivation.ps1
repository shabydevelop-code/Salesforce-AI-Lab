# Prepare an app-scoped Home page override using current org metadata.
# Does not deploy or activate anything.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
Set-Location $root
$org = 'SalesforceDev'
$staging = 'Packages/ServiceWorkspace/retrieved-metadata'
$destination = 'Packages/ServiceWorkspace/force-app/main/default/applications/standard__Service.app-meta.xml'
$page = 'Packages/ServiceWorkspace/force-app/main/default/flexipages/Service_Representative_Home.flexipage-meta.xml'
if (-not (Get-Command sf -ErrorAction SilentlyContinue)) { throw 'Salesforce CLI not found.' }
if (-not (Test-Path -LiteralPath $page)) { throw "Missing Home page: $page" }
New-Item -ItemType Directory -Path $staging -Force | Out-Null
& sf project retrieve start --metadata 'CustomApplication:standard__Service' --target-org $org --output-dir $staging
if ($LASTEXITCODE -ne 0) { throw 'Could not retrieve the current Service application. Nothing was changed.' }
$source = Get-ChildItem -LiteralPath $staging -Recurse -Filter 'standard__Service.app-meta.xml' -File | Select-Object -First 1
# The standard Service app cannot accept Flexipage Home action overrides.
# Do not generate invalid metadata or alter the standard application.
if (Test-Path -LiteralPath $destination) {
    Write-Warning "Previously generated activation metadata exists: $destination. Do not deploy it."
}
throw 'Unsupported target: standard__Service is a standard app. Flexipage Home overrides require a Lightning app. No metadata was generated or deployed. Use a custom Lightning app or another supported assignment method.'
if (-not $source) { throw 'Retrieved Service application XML not found. Nothing was changed.' }
[xml]$doc = Get-Content -LiteralPath $source.FullName -Raw -Encoding UTF8
$ns = $doc.DocumentElement.NamespaceURI
$manager = New-Object System.Xml.XmlNamespaceManager($doc.NameTable)
$manager.AddNamespace('m', $ns)
$existing = @($doc.SelectNodes('/m:CustomApplication/m:actionOverrides', $manager) | Where-Object {
    $_.SelectSingleNode('m:actionName', $manager).InnerText -eq 'View' -and
    $_.SelectSingleNode('m:pageOrSobjectType', $manager).InnerText -eq 'standard-home' -and
    $_.SelectSingleNode('m:formFactor', $manager).InnerText -eq 'Large'
})
if ($existing.Count -gt 1) { throw 'Multiple desktop Home overrides found. Refusing to modify.' }
foreach ($node in $existing) { [void]$doc.DocumentElement.RemoveChild($node) }
$override = $doc.CreateElement('actionOverrides', $ns)
foreach ($pair in @(@('actionName','View'),@('content','Service_Representative_Home'),@('formFactor','Large'),@('pageOrSobjectType','standard-home'),@('type','Flexipage'))) {
    $child = $doc.CreateElement($pair[0], $ns)
    $child.InnerText = $pair[1]
    [void]$override.AppendChild($child)
}
# Metadata schema expects actionOverrides before brand and navigation properties.
$first = $doc.DocumentElement.FirstChild
if ($first) { [void]$doc.DocumentElement.InsertBefore($override, $first) } else { [void]$doc.DocumentElement.AppendChild($override) }
$folder = Split-Path -Parent $destination
New-Item -ItemType Directory -Path $folder -Force | Out-Null
$settings = New-Object System.Xml.XmlWriterSettings
$settings.Indent = $true
$settings.Encoding = New-Object System.Text.UTF8Encoding($false)
$writer = [System.Xml.XmlWriter]::Create((Join-Path $root $destination), $settings)
try { $doc.Save($writer) } finally { $writer.Dispose() }
Write-Host "Prepared app metadata: $destination"
Write-Host 'No Salesforce deployment or activation has occurred.'
Write-Host 'Next: validate this file with Salesforce CLI.'
