param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "asia-northeast3",

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
$freezeTag = git rev-parse refs/tags/ecr-poc-v3-freeze
if ($LASTEXITCODE -ne 0 -or $head -ne $originMain -or $head -ne $freezeTag) {
    throw "HEAD, origin/main, and ecr-poc-v3-freeze must identify the same commit."
}

$projectNumber = gcloud projects describe $ProjectId --format "value(projectNumber)"
$bucketName = "ecr-poc-$projectNumber-$Region"
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$suffix = [guid]::NewGuid().ToString("N").Substring(0, 8)
$runId = "cloud-v3-$timestamp-$suffix"

$executionName = gcloud run jobs execute ecr-poc-evaluate `
    --project $ProjectId `
    --region $Region `
    --update-env-vars "ECR_RUN_ID=$runId" `
    --wait `
    --format "value(metadata.name)" `
    --quiet
if ($LASTEXITCODE -ne 0) {
    throw "Cloud Run Job failed. The failed run is retained and will not be published."
}

Write-Output "runId=$runId"
Write-Output "execution=$executionName"
Write-Output "result=gs://$bucketName/runs/$runId/evaluation.json"
Write-Output "published=false"
