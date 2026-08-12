param(
    [string]$Token = $env:GITHUB_TOKEN
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

if ($Token) {
    $env:GITHUB_TOKEN = $Token
} else {
    Write-Warning "Không có GITHUB_TOKEN. Chương trình vẫn chạy nhưng hạn mức API thấp hơn."
}

python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

python -m repo_scout
exit $LASTEXITCODE

