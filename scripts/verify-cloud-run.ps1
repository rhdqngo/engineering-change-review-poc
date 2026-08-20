param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "asia-northeast3"
)

$ErrorActionPreference = "Stop"

$projectNumber = gcloud projects describe $ProjectId --format "value(projectNumber)"
$bucketName = "ecr-poc-$projectNumber-$Region"
$expectedWebAccount = "ecr-poc-web@$ProjectId.iam.gserviceaccount.com"
$expectedJobAccount = "ecr-poc-job@$ProjectId.iam.gserviceaccount.com"

$service = gcloud run services describe ecr-poc `
    --project $ProjectId `
    --region $Region `
    --platform managed `
    --format json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) {
    throw "Unable to describe the Cloud Run service."
}
$job = gcloud run jobs describe ecr-poc-evaluate `
    --project $ProjectId `
    --region $Region `
    --format json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) {
    throw "Unable to describe the Cloud Run Job."
}

if ($service.spec.template.spec.serviceAccountName -ne $expectedWebAccount) {
    throw "Cloud Run service is not using the dedicated web identity."
}
if ($job.spec.template.spec.template.spec.serviceAccountName -ne $expectedJobAccount) {
    throw "Cloud Run Job is not using the dedicated job identity."
}
$serviceRevision = gcloud run revisions describe $service.status.latestReadyRevisionName `
    --project $ProjectId `
    --region $Region `
    --format json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($serviceRevision.status.imageDigest)) {
    throw "Unable to resolve the service image digest."
}
if ($serviceRevision.status.imageDigest -ne $job.spec.template.spec.template.spec.containers[0].image) {
    throw "Cloud Run service and Job image digests differ."
}

$serviceUrl = $service.status.url
$identityToken = gcloud auth print-identity-token
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($identityToken)) {
    throw "Unable to obtain an identity token."
}
$headers = @{ Authorization = "Bearer $identityToken" }
$unauthenticatedStatus = $null
try {
    Invoke-WebRequest -Uri "$serviceUrl/health" -UseBasicParsing | Out-Null
    $unauthenticatedStatus = 200
} catch {
    if ($null -ne $_.Exception.Response) {
        $unauthenticatedStatus = [int]$_.Exception.Response.StatusCode
    }
}
if ($unauthenticatedStatus -ne 403) {
    throw "Unauthenticated Cloud Run requests must return 403; got $unauthenticatedStatus."
}
$health = Invoke-RestMethod -Uri "$serviceUrl/health" -Headers $headers
if (
    $health.status -ne "ok" -or
    $health.data_freeze -ne "valid" -or
    $health.result_store -ne "gcs" -or
    [string]::IsNullOrWhiteSpace($health.published_run_id)
) {
    throw "Cloud health response did not validate the GCS-published experiment."
}
$caseCatalog = Invoke-RestMethod -Uri "$serviceUrl/api/cases" -Headers $headers
if ($caseCatalog.top_k -ne 6 -or $caseCatalog.cases.Count -ne 18) {
    throw "Cloud case catalog does not match the frozen experiment."
}
$evaluation = Invoke-RestMethod -Uri "$serviceUrl/api/evaluation" -Headers $headers
if (
    $evaluation.experiment_id -ne "ecr-poc-preregistered-v3" -or
    $evaluation.cases.Count -ne 18 -or
    $evaluation.run_id -ne $health.published_run_id
) {
    throw "Published Cloud evaluation is not the complete v3 run."
}

$env:UV_CACHE_DIR = ".cache\uv"
uv run ecr-poc verify-published --bucket $bucketName
if ($LASTEXITCODE -ne 0) {
    throw "Published GCS pointer verification failed."
}

$forbiddenRoles = gcloud projects get-iam-policy $ProjectId `
    --flatten "bindings[].members" `
    --filter "bindings.members:(serviceAccount:$expectedWebAccount OR serviceAccount:$expectedJobAccount) AND bindings.role:(roles/editor OR roles/owner OR roles/storage.admin)" `
    --format "value(bindings.role)"
if (-not [string]::IsNullOrWhiteSpace($forbiddenRoles)) {
    throw "A dedicated runtime identity has a forbidden broad project role: $forbiddenRoles"
}

$projectPolicy = gcloud projects get-iam-policy $ProjectId --format json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) {
    throw "Unable to read project IAM policy."
}
$webProjectRoles = @(
    $projectPolicy.bindings | Where-Object {
        $_.members -contains "serviceAccount:$expectedWebAccount"
    } | ForEach-Object { $_.role }
)
$jobProjectRoles = @(
    $projectPolicy.bindings | Where-Object {
        $_.members -contains "serviceAccount:$expectedJobAccount"
    } | ForEach-Object { $_.role }
)
if ($webProjectRoles.Count -ne 0) {
    throw "Web identity must not have project-level roles: $webProjectRoles"
}
if ($jobProjectRoles.Count -ne 1 -or $jobProjectRoles[0] -ne "roles/aiplatform.user") {
    throw "Job identity project access is not exactly aiplatform.user."
}

$bucketPolicy = gcloud storage buckets get-iam-policy "gs://$bucketName" --format json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) {
    throw "Unable to read the dedicated bucket IAM policy."
}
$webBindings = @(
    $bucketPolicy.bindings | Where-Object {
        $_.members -contains "serviceAccount:$expectedWebAccount"
    } | ForEach-Object { $_.role }
)
$jobBindings = @(
    $bucketPolicy.bindings | Where-Object {
        $_.members -contains "serviceAccount:$expectedJobAccount"
    } | ForEach-Object { $_.role }
)
if ($webBindings.Count -ne 1 -or $webBindings[0] -ne "roles/storage.objectViewer") {
    throw "Web identity bucket access is not exactly storage.objectViewer."
}
if ($jobBindings.Count -ne 1 -or $jobBindings[0] -ne "roles/storage.objectUser") {
    throw "Job identity bucket access is not exactly storage.objectUser."
}

$logRecords = gcloud logging read `
    "resource.type=cloud_run_job AND resource.labels.job_name=ecr-poc-evaluate AND jsonPayload.run_id=$($health.published_run_id)" `
    --project $ProjectId `
    --limit 200 `
    --format json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) {
    throw "Structured Cloud Logging read failed."
}
$events = @($logRecords | ForEach-Object { $_.jsonPayload.event })
if (
    @($events | Where-Object { $_ -eq "job_started" }).Count -ne 1 -or
    @($events | Where-Object { $_ -eq "case_completed" }).Count -ne 18 -or
    @($events | Where-Object { $_ -eq "evaluation_completed" }).Count -ne 1
) {
    throw "Structured logs do not contain one start, 18 terminal cases, and one completion."
}
$serializedLogs = $logRecords | ConvertTo-Json -Depth 20
if ($serializedLogs -match '"(prompt|raw_output|evidence|credential|token)"\s*:') {
    throw "Structured logs contain a prohibited sensitive or raw-content field."
}

Write-Output "health=ok"
Write-Output "dataFreeze=valid"
Write-Output "resultStore=gcs"
Write-Output "publishedRun=$($health.published_run_id)"
Write-Output "topK=$($caseCatalog.top_k)"
Write-Output "cases=$($caseCatalog.cases.Count)"
Write-Output "webServiceAccount=$expectedWebAccount"
Write-Output "jobServiceAccount=$expectedJobAccount"
