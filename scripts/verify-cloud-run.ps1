param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "asia-northeast3"
)

$ErrorActionPreference = "Stop"

$serviceUrl = gcloud run services describe ecr-poc `
    --project $ProjectId `
    --region $Region `
    --platform managed `
    --format "value(status.url)"

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($serviceUrl)) {
    throw "Unable to resolve the Cloud Run service URL."
}

$identityToken = gcloud auth print-identity-token
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($identityToken)) {
    throw "Unable to obtain an identity token."
}

$headers = @{ Authorization = "Bearer $identityToken" }
$health = Invoke-RestMethod -Uri "$serviceUrl/health" -Headers $headers
if ($health.status -ne "ok" -or $health.data_freeze -ne "valid") {
    throw "Cloud health response did not validate the frozen data."
}

$caseCatalog = Invoke-RestMethod -Uri "$serviceUrl/api/cases" -Headers $headers
if ($caseCatalog.top_k -ne 6 -or $caseCatalog.cases.Count -ne 18) {
    throw "Cloud case catalog does not match the frozen experiment."
}

Write-Output "health=ok"
Write-Output "dataFreeze=valid"
Write-Output "topK=$($caseCatalog.top_k)"
Write-Output "cases=$($caseCatalog.cases.Count)"

gcloud run services logs read ecr-poc `
    --project $ProjectId `
    --region $Region `
    --platform managed `
    --limit 50

if ($LASTEXITCODE -ne 0) {
    throw "Cloud Logging read failed."
}
