# Cloud Run Deployment Log

status: deployed-and-verified  
region: `asia-northeast3`  
service: `ecr-poc`  
updated: 2026-08-20

## V2 completion status

The original v1 service history remains below. V2 provisioning, same-digest service/Job deployment, and a valid first 18-case execution/publication completed. Independent browser audit rejected the deployed provenance presentation because the run ID was ambiguously truncated and the footer called v2 a legacy freeze. The immutable run remains in GCS; a corrected remote freeze and full rerun will establish the final accepted result.

The first approved v2 provisioning attempt created `ecr-poc-912838451352-asia-northeast3` with uniform bucket-level access, then stopped before service-account, IAM, or upload steps. The installed gcloud release rejected value-form PAP/versioning flags; the script was corrected to the supported boolean flags and must be re-frozen before the idempotent retry. No v2 model call occurred.

The corrective retry completed bucket hardening, dedicated identities, IAM, frozen/historical uploads, and deployed private revision `ecr-poc-00003-wn5` plus the evaluation Job at image digest `sha256:091dd2d1d37f35d45f47ce733afda87c1432e92750be785d8b626175f4e3bd88`. Pre-run inspection stopped execution because PowerShell serialized the five Job arguments as one string and the verifier used an incorrect Job JSON path. Both defects are being re-frozen before redeployment; no v2 model call occurred.

## Approved attempt 1

The user approved Cloud Build enablement and a private Cloud Run deployment. The prepared scale-to-zero deployment was invoked with unauthenticated access disabled.

Observed external state:

- `cloudbuild.googleapis.com` was enabled successfully.
- The regional `cloud-run-source-deploy` Artifact Registry repository was created.
- Source upload completed.
- The build did not start because the project-selected default Compute service account lacked required build IAM.
- No `ecr-poc` Cloud Run service was created.

## Approved least-privilege correction

Google's documented source-deploy path supports a user-specified build identity. After the user explicitly approved the exact IAM and billable deployment payload, the deployment created `ecr-poc-build`, granted only project-level `roles/run.builder` to that identity, granted the active deployer `roles/iam.serviceAccountUser` on that identity only, and passed it through `--build-service-account`.

No permission was added before that exact approval, and no broader IAM role was granted.

## Final deployment

- Cloud Build built the repository Dockerfile successfully.
- Final revision `ecr-poc-00002-v9g` serves 100% of traffic with unauthenticated access disabled, minimum instances 0, and maximum instances 1.
- The first revision exposed a deployment-only UI defect: `results/latest.json` had been overwritten by a fixture run. The application was corrected to pin the reported experiment artifact `results/runs/vertex-adk.json`; the raw artifact and freeze were unchanged.
- Authenticated `/health` returned `status=ok` and `dataFreeze=valid`; `/api/cases` returned Top-K 6 and all 18 frozen cases.
- `/api/evaluation` returned provider `vertex-adk`; the retained raw artifact still had SHA-256 `7832aad0728660c2283cfa41aedddf06a34e3b50e7fd6d514e0d0854b69ee28e`.

## Browser and logging evidence

- The authenticated browser flow displayed `SAVED EVALUATION · vertex-adk · gemini-3.5-flash`.
- Representative results matched the raw artifact: DIR-02 4/0, XART-03 2/0, CLN-01 0/0, and CLN-02 2/0 verified/blocked. CLN-02 is the reported restore false alarm.
- The injected fixture rejection showed 1 blocked output, `No evidence exposed.`, and blocking stage `deterministic_exact_span`.
- An unauthenticated `/health` request returned HTTP 403.
- Cloud Logging recorded revision startup and 200 responses for `/`, `/api/cases`, DIR-02, XART-03, CLN-01, CLN-02, and fixture rejection paths, plus the expected unauthenticated 403.
- Browser capture: `docs/ui/evidence/review-docket-cloud-run.png`.

## Recovery / removal

The private service, build identity, source repository, and enabled APIs are retained as the requested operational PoC. Removing any of them requires a separate explicit destructive-action approval.
