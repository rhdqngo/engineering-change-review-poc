param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [Parameter(Mandatory = $true)]
    [string]$RunId,

    [Parameter(Mandatory = $true)]
    [string]$ExperimentManifest,

    [Parameter(Mandatory = $true)]
    [string]$FreezeTag,

    [Parameter(Mandatory = $true)]
    [string]$SourceCommit,

    [string]$RunPrefix = "runs/v6",

    [string]$PublishedObject = "published/v6/demo.json",

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
$freezeCommit = git rev-parse "refs/tags/$FreezeTag"
if (
    $LASTEXITCODE -ne 0 -or
    $head -ne $SourceCommit -or
    $head -ne $originMain -or
    $head -ne $freezeCommit
) {
    throw "HEAD, requested source commit, origin/main, and requested freeze tag must identify the same commit."
}
$manifestPath = Join-Path "data/experiments" $ExperimentManifest
if ((Split-Path -Leaf $ExperimentManifest) -ne $ExperimentManifest -or -not (Test-Path -LiteralPath $manifestPath)) {
    throw "ExperimentManifest must name an existing manifest leaf in data/experiments."
}
$experiment = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($experiment.freeze_tag -ne $FreezeTag) {
    throw "Experiment manifest freeze tag does not match -FreezeTag."
}
if (
    $RunPrefix -eq 'runs' -or
    $RunPrefix -match '^runs/v[1-5](?:/|$)' -or
    $PublishedObject -eq 'published/demo.json' -or
    $PublishedObject -match '^published/v[1-5](?:/|$)'
) {
    throw "Refusing to publish v6 into a historical v1-v5 GCS namespace."
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
    --source-commit $SourceCommit `
    --experiment-manifest $ExperimentManifest `
    --run-prefix $RunPrefix `
    --published-object $PublishedObject
if ($LASTEXITCODE -ne 0) {
    throw "Completed run validation/publication failed."
}

Write-Output "runId=$RunId"
Write-Output "published=gs://$bucketName/$PublishedObject"
