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

    [string]$RunPrefix = "runs/v6",

    [string]$PublishedObject = "published/v6/demo.json",

    [string]$AuthenticatedBaseUrl = ""
)

$ErrorActionPreference = "Stop"

$manifestPath = Join-Path "data/experiments" $ExperimentManifest
if ((Split-Path -Leaf $ExperimentManifest) -ne $ExperimentManifest -or -not (Test-Path -LiteralPath $manifestPath)) {
    throw "ExperimentManifest must name an existing manifest leaf in data/experiments."
}
$experiment = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($experiment.freeze_tag -ne $FreezeTag) {
    throw "Experiment manifest freeze tag does not match -FreezeTag."
}
$freezeCommit = git rev-parse "refs/tags/$FreezeTag"
if ($LASTEXITCODE -ne 0 -or $freezeCommit -ne $SourceCommit) {
    throw "Requested freeze tag does not identify the requested source commit."
}
if (
    $RunPrefix -eq 'runs' -or
    $RunPrefix -match '^runs/v[1-5](?:/|$)' -or
    $PublishedObject -eq 'published/demo.json' -or
    $PublishedObject -match '^published/v[1-5](?:/|$)'
) {
    throw "Refusing to verify v6 through a historical v1-v5 GCS namespace."
}

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

function ConvertTo-EnvironmentMap($items) {
    $values = @{}
    foreach ($item in @($items)) {
        $values[$item.name] = $item.value
    }
    return $values
}

$serviceEnvironment = ConvertTo-EnvironmentMap $service.spec.template.spec.containers[0].env
$jobEnvironment = ConvertTo-EnvironmentMap $job.spec.template.spec.template.spec.containers[0].env
if (
    $serviceEnvironment.ECR_PUBLISHED_OBJECT -ne $PublishedObject -or
    $serviceEnvironment.ECR_FREEZE_VERSION -ne $experiment.experiment_id -or
    $serviceEnvironment.ECR_SOURCE_COMMIT -ne $SourceCommit -or
    $serviceEnvironment.ECR_LIVE_PROVIDER -ne "vertex-adk" -or
    $serviceEnvironment.ECR_LIVE_EMBEDDING -ne "vertex"
) {
    throw "Cloud Run service environment does not match the requested v6 identity."
}
if (
    $jobEnvironment.ECR_EXPERIMENT_MANIFEST -ne $ExperimentManifest -or
    $jobEnvironment.ECR_GCS_RUN_PREFIX -ne $RunPrefix -or
    $jobEnvironment.ECR_SOURCE_COMMIT -ne $SourceCommit
) {
    throw "Cloud Run Job environment does not match the requested v6 identity."
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

$servicePolicy = gcloud run services get-iam-policy ecr-poc `
    --project $ProjectId `
    --region $Region `
    --format json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) {
    throw "Unable to read Cloud Run service IAM policy."
}
$publicMembers = @(
    $servicePolicy.bindings | ForEach-Object { $_.members } | Where-Object {
        $_ -in @("allUsers", "allAuthenticatedUsers")
    }
)
if ($publicMembers.Count -ne 0) {
    throw "Cloud Run service has a public invoker binding: $publicMembers"
}
$activeAccount = gcloud config get-value account 2>$null
$activeInvokerRoles = @(
    $servicePolicy.bindings | Where-Object {
        $_.members -contains "user:$activeAccount"
    } | ForEach-Object { $_.role }
)
if (
    [string]::IsNullOrWhiteSpace($activeAccount) -or
    $activeInvokerRoles.Count -ne 1 -or
    $activeInvokerRoles[0] -ne "roles/run.invoker"
) {
    throw "Active verifier account must have only service-level roles/run.invoker."
}

$serviceUrl = $service.status.url.TrimEnd("/")
$authenticatedUrl = $AuthenticatedBaseUrl.TrimEnd("/")
$headers = @{}
if ([string]::IsNullOrWhiteSpace($authenticatedUrl)) {
    $authenticatedUrl = $serviceUrl
    $identityToken = gcloud auth print-identity-token
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($identityToken)) {
        throw "Unable to obtain an identity token."
    }
    $headers = @{ Authorization = "Bearer $identityToken" }
}

function Invoke-AuthenticatedGet([string]$Path) {
    $parameters = @{ Uri = "$authenticatedUrl/$Path" }
    if ($headers.Count -ne 0) {
        $parameters.Headers = $headers
    }
    return Invoke-RestMethod @parameters
}

$unauthenticatedStatus = $null
try {
    Invoke-WebRequest -Uri "$serviceUrl/health" -UseBasicParsing | Out-Null
    $unauthenticatedStatus = 200
} catch {
    if ($null -ne $_.Exception.Response) {
        $unauthenticatedStatus = [int]$_.Exception.Response.StatusCode
    }
}
if ($unauthenticatedStatus -notin @(403, 404)) {
    throw "Unauthenticated Cloud Run requests must be denied with 403 or 404; got $unauthenticatedStatus."
}
$health = Invoke-AuthenticatedGet "health"
if ($health.status -ne "alive") {
    throw "Cloud liveness endpoint failed."
}
$readiness = Invoke-AuthenticatedGet "readyz"
$integrity = Invoke-AuthenticatedGet "integrity"
if (
    $readiness.status -ne "ready" -or
    $readiness.data_integrity -ne "valid" -or
    $readiness.result_store -ne "gcs" -or
    $readiness.source_commit -ne $SourceCommit -or
    $integrity.status -ne "valid" -or
    $integrity.active_experiment_id -ne $experiment.experiment_id -or
    [string]::IsNullOrWhiteSpace($readiness.embedding_index_fingerprint) -or
    [string]::IsNullOrWhiteSpace($readiness.identifier_index_fingerprint) -or
    [string]::IsNullOrWhiteSpace($readiness.published_run_id)
) {
    throw "Cloud readiness/integrity response did not validate the GCS-published experiment."
}
$caseCatalog = Invoke-AuthenticatedGet "api/cases"
if ($caseCatalog.top_k -ne 10 -or $caseCatalog.cases.Count -ne 20) {
    throw "Cloud case catalog does not match the frozen experiment."
}
$evaluation = Invoke-AuthenticatedGet "api/evaluation"
if (
    $evaluation.experiment_id -ne $experiment.experiment_id -or
    $evaluation.cases.Count -ne 20 -or
    $evaluation.run_id -ne $readiness.published_run_id
) {
    throw "Published Cloud evaluation is not the complete requested run."
}

$env:UV_CACHE_DIR = ".cache\uv"
uv run ecr-poc verify-published --bucket $bucketName --published-object $PublishedObject
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
if ($webProjectRoles.Count -ne 1 -or $webProjectRoles[0] -ne "roles/aiplatform.user") {
    throw "Web identity project access is not exactly aiplatform.user."
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
    "resource.type=cloud_run_job AND resource.labels.job_name=ecr-poc-evaluate AND jsonPayload.run_id=$($readiness.published_run_id) AND jsonPayload.event:*" `
    --project $ProjectId `
    --limit 500 `
    --format json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) {
    throw "Structured Cloud Logging read failed."
}
$events = @($logRecords | ForEach-Object { $_.jsonPayload.event })
if (
    @($events | Where-Object { $_ -eq "job_started" }).Count -ne 1 -or
    @($events | Where-Object { $_ -eq "case_completed" }).Count -ne 20 -or
    @($events | Where-Object { $_ -eq "evaluation_completed" }).Count -ne 1
) {
    throw "Structured logs do not contain one start, 20 terminal cases, and one completion."
}
$serializedLogs = $logRecords | ConvertTo-Json -Depth 20
if ($serializedLogs -match '"(prompt|raw_output|evidence|credential|token)"\s*:') {
    throw "Structured logs contain a prohibited sensitive or raw-content field."
}

Write-Output "liveness=alive"
Write-Output "unauthenticatedStatus=$unauthenticatedStatus"
Write-Output "readiness=ready"
Write-Output "integrity=valid"
Write-Output "resultStore=gcs"
Write-Output "publishedRun=$($readiness.published_run_id)"
Write-Output "publishedObject=$PublishedObject"
Write-Output "runPrefix=$RunPrefix"
Write-Output "topK=$($caseCatalog.top_k)"
Write-Output "cases=$($caseCatalog.cases.Count)"
Write-Output "webServiceAccount=$expectedWebAccount"
Write-Output "jobServiceAccount=$expectedJobAccount"
