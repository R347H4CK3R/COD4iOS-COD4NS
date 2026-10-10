# IW5 asset listing verification — Windows
# Requires official OpenAssetTools Unlinker (tested v0.33.0).
# Reads the user's local retail files and reports asset listing success.
param(
  [Parameter(Mandatory=$true)][string]$GameRoot,
  [Parameter(Mandatory=$true)][string]$Unlinker
)
$ErrorActionPreference = "Stop"
if(!(Test-Path -LiteralPath $Unlinker)){throw "Unlinker missing"}
$zones = @("zone/english/mp_dome.ff", "zone/dlc/mp_boardwalk.ff", "zone/english/so_survival_mp_dome.ff")
$summary = @()
foreach($zone in $zones){
  $path = Join-Path $GameRoot $zone
  if(!(Test-Path -LiteralPath $path)){throw "Missing zone: $zone"}
  $lines = & $Unlinker --no-color --list $path 2>&1
  $exit = $LASTEXITCODE
  $finish = ($lines | Select-String '^Finished with .* warnings, .* errors' | Select-Object -Last 1).Line
  $summary += [pscustomobject]@{Zone=$zone;ExitCode=$exit;Result=$finish;OutputLines=$lines.Count}
  if($exit -ne 0 -or $finish -notmatch 'Finished with 0 warnings, 0 errors'){throw "Asset list failed: $zone : $finish"}
}
$summary | Format-Table -AutoSize
