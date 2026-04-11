param(
    [string]$SourcePath = (Join-Path $PSScriptRoot "..\..\data\puppy_tracker.db"),
    [string]$DestinationPath = (Join-Path $PSScriptRoot "..\data\puppy_tracker_test.db")
)

$resolvedSource = (Resolve-Path -LiteralPath $SourcePath).Path
$destinationDirectory = Split-Path -Parent $DestinationPath

if (-not (Test-Path -LiteralPath $destinationDirectory)) {
    New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
}

Copy-Item -LiteralPath $resolvedSource -Destination $DestinationPath -Force

Write-Output "Refreshed test database from $resolvedSource to $DestinationPath"
