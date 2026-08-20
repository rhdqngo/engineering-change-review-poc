param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [Parameter(Mandatory = $true)]
    [string]$RunId,

    [string]$Region = "asia-northeast3",

    [switch]$ApprovePublish
)

$ErrorActionPreference = "Stop"

if (-not $ApprovePublish) {
    throw "Refusing to change the published GCS pointer without -ApprovePublish."
}

$status = git status --porcelain
if (-not [string]::IsNullOrWhiteSpace($status)) {
    throw "Refusing to publish from a dirty worktree."
}
$head = git rev-parse HEAD
$originMain = git rev-parse origin/main
$freezeTag = git rev-parse refs/tags/ecr-poc-v3-freeze
if ($LASTEXITCODE -ne 0 -or $head -ne $originMain -or $head -ne $freezeTag) {
    throw "HEAD, origin/main, and ecr-poc-v3-freeze must identify the same commit."
}

$projectNumber = gcloud projects describe $ProjectId --format "value(projectNumber)"
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($projectNumber)) {
    throw "Unable to resolve the GCP project number."
}
$bucketName = "ecr-poc-$projectNumber-$Region"

$env:UV_CACHE_DIR = ".cache\uv"
uv run ecr-poc publish-run `
    --bucket $bucketName `
    --run-id $RunId `
    --source-commit $head `
    --experiment-manifest ecr-poc-v3.json
if ($LASTEXITCODE -ne 0) {
    throw "Completed run validation/publication failed."
}

Write-Output "runId=$RunId"
Write-Output "published=gs://$bucketName/published/demo.json"
