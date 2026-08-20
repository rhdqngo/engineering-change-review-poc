param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "asia-northeast3",

    [Parameter(Mandatory = $true)]
    [string]$ExperimentManifest,

    [Parameter(Mandatory = $true)]
    [string]$FreezeTag,

    [Parameter(Mandatory = $true)]
    [string]$SourceCommit,

    [string]$RunPrefix = "runs/v5",

    [switch]$ApproveBillableRun
)

$ErrorActionPreference = "Stop"

if (-not $ApproveBillableRun) {
    throw "Refusing to execute the billable 18-case Vertex run without -ApproveBillableRun."
}

$status = git status --porcelain
if (-not [string]::IsNullOrWhiteSpace($status)) {
    throw "Refusing to execute from a dirty worktree."
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
if ($RunPrefix -eq 'runs' -or $RunPrefix -match '^runs/v[1-4](?:/|$)') {
    throw "Refusing to write a v5 run into a historical v1-v4 GCS prefix."
}

$projectNumber = gcloud projects describe $ProjectId --format "value(projectNumber)"
$bucketName = "ecr-poc-$projectNumber-$Region"
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$suffix = [guid]::NewGuid().ToString("N").Substring(0, 8)
$experimentSuffix = $experiment.experiment_id -replace '^ecr-poc-preregistered-', ''
$runId = "cloud-$experimentSuffix-$timestamp-$suffix"

$executionName = gcloud run jobs execute ecr-poc-evaluate `
    --project $ProjectId `
    --region $Region `
    --update-env-vars "ECR_RUN_ID=$runId,ECR_SOURCE_COMMIT=$SourceCommit,ECR_EXPERIMENT_MANIFEST=$ExperimentManifest,ECR_GCS_RUN_PREFIX=$RunPrefix" `
    --wait `
    --format "value(metadata.name)" `
    --quiet
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($executionName)) {
    throw "Cloud Run Job failed. The failed run is retained and will not be published."
}

Write-Output "runId=$runId"
Write-Output "execution=$executionName"
Write-Output "result=gs://$bucketName/$RunPrefix/$runId/evaluation.json"
Write-Output "published=false"
