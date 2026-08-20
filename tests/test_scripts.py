from ecr_poc.data import repository_root


def _script(name: str) -> str:
    return (repository_root() / "scripts" / name).read_text(encoding="utf-8")


def test_mutating_cloud_scripts_require_explicit_v6_identity_and_approval() -> None:
    approval_switches = {
        "provision-gcp.ps1": "ApproveBillableResources",
        "deploy-cloud-run.ps1": "ApproveBillableResources",
        "run-cloud-evaluation.ps1": "ApproveBillableRun",
        "publish-cloud-evaluation.ps1": "ApprovePublish",
    }
    for name, approval in approval_switches.items():
        script = _script(name)
        assert "[string]$ExperimentManifest" in script
        assert "[string]$FreezeTag" in script
        assert "[string]$SourceCommit" in script
        assert f"[switch]${approval}" in script
        assert "refs/tags/$FreezeTag" in script
        assert "$head -ne $SourceCommit" in script


def test_v6_cloud_scripts_reject_historical_gcs_namespaces() -> None:
    provision = _script("provision-gcp.ps1")
    deploy = _script("deploy-cloud-run.ps1")
    run = _script("run-cloud-evaluation.ps1")
    publish = _script("publish-cloud-evaluation.ps1")
    verify = _script("verify-cloud-run.ps1")

    assert "historical v1-v5 GCS prefix" in provision
    for script in (deploy, publish, verify):
        assert "$PublishedObject -eq 'published/demo.json'" in script
        assert "historical v1-v5 GCS namespace" in script
    for script in (deploy, run, publish, verify):
        assert "$RunPrefix -eq 'runs'" in script
    assert '--concurrency 1 `' in deploy
    assert '--timeout 300 `' in deploy
    assert 'ECR_LIVE_PROVIDER=vertex-adk' in deploy
    assert 'ECR_LIVE_EMBEDDING=vertex' in deploy
    assert '--role "roles/aiplatform.user"' in provision


def test_cloud_verification_binds_deployed_state_to_requested_identity() -> None:
    verify = _script("verify-cloud-run.ps1")
    assert '$freezeCommit = git rev-parse "refs/tags/$FreezeTag"' in verify
    assert "$freezeCommit -ne $SourceCommit" in verify
    assert "$serviceEnvironment.ECR_PUBLISHED_OBJECT -ne $PublishedObject" in verify
    assert "$serviceEnvironment.ECR_FREEZE_VERSION -ne $experiment.experiment_id" in verify
    assert "$jobEnvironment.ECR_EXPERIMENT_MANIFEST -ne $ExperimentManifest" in verify
    assert "$jobEnvironment.ECR_GCS_RUN_PREFIX -ne $RunPrefix" in verify
    assert "$readiness.source_commit -ne $SourceCommit" in verify
    assert '[string]$AuthenticatedBaseUrl = ""' in verify
    assert '$unauthenticatedStatus -notin @(403, 404)' in verify
    assert '$_ -in @("allUsers", "allAuthenticatedUsers")' in verify
    assert '$activeInvokerRoles[0] -ne "roles/run.invoker"' in verify
    assert '$webProjectRoles[0] -ne "roles/aiplatform.user"' in verify
    assert '$jobProjectRoles[0] -ne "roles/aiplatform.user"' in verify
    assert "$readiness.identifier_index_fingerprint" in verify
    assert '$_ -eq "case_completed" }).Count -ne 20' in verify
    assert "AND jsonPayload.event:*" in verify
    assert "--limit 500" in verify
