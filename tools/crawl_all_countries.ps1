param(
  [int]$Limit = 100,
  [int]$Concurrency = 2,
  [double]$MinDelay = 2,
  [double]$MaxDelay = 4,
  [string]$Site = 'amazon_us'
)

$ErrorActionPreference = 'Stop'
$repo = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $repo

$python = Join-Path $repo '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw "venv python not found: $python" }

$countries = @('kr', 'vn', 'th', 'tw', 'hk', 'mo', 'jp')

foreach ($country in $countries) {
  $outDir = Join-Path $repo "data\crawls\out_${Site}_${country}_$Limit"
  Write-Host "=== [$country] crawl start -> $outDir ==="
  & $python -m app crawl --site $Site --country $country --limit $Limit --concurrency $Concurrency --min-delay $MinDelay --max-delay $MaxDelay --out $outDir --verbose
  if ($LASTEXITCODE -ne 0) {
    Write-Host "=== [$country] crawl FAILED (exit=$LASTEXITCODE), skipping publish ==="
    continue
  }

  Write-Host "=== [$country] publish start ==="
  powershell -ExecutionPolicy Bypass -File (Join-Path $repo 'tools\publish.ps1') -OutDir $outDir -DataDir (Join-Path $repo 'dashboard\data') -Site $Site -Country $country -Limit $Limit
  if ($LASTEXITCODE -ne 0) {
    Write-Host "=== [$country] publish FAILED (exit=$LASTEXITCODE) ==="
    continue
  }
  Write-Host "=== [$country] DONE ==="
}

Write-Host "=== ALL COUNTRIES FINISHED ==="
