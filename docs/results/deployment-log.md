# Cloud Run Deployment Log

status: deployed-and-verified  
region: `asia-northeast3`  
service: `ecr-poc`  
updated: 2026-08-20

## V5 completion status

V5 is complete. Both lightweight freeze tags identify implementation commit `4d1519f84cd5bac836ea8125ee2d63525ad2578d`; v1-v4 tags and GCS objects remain unchanged. Revision `ecr-poc-00008-pk2` and Job `ecr-poc-evaluate` use image digest `sha256:8f4cc7cf8fa04e5832b83634b45c5139868ee7d2f8f0d56c929a49521bbe8afd`.

| Item | Baseline | Q1 comparison |
| --- | --- | --- |
| Freeze tag | `ecr-poc-v5-freeze` | `ecr-poc-v5-q1-freeze` |
| Execution | `ecr-poc-evaluate-2s5kv` | `ecr-poc-evaluate-l9mjm` |
| Run | `cloud-v5-20260820T072055Z-3efe8584` | `cloud-v5-q1-20260820T074302Z-26e9b5e5` |
| Generation | `1787210878757222` | `1787212289859637` |
| SHA-256 | `d04c26087b1436a956dd18ac353417c6ebcd8db828522c0fb9265516ede143ef` | `2e3b185f548eeff405e816e0c607edc11db46c8fac9c2f42dd369cd0a7a6cae2` |
| Pointer | `published/v5/demo.json` | `published/v5-q1/comparison.json` |

Provisioning uploaded 30 immutable objects under `frozen/ecr-poc-v5`. Both single-task runs completed 18/18 cases with zero role errors and the same embedding fingerprint. The service and Job retain their dedicated runtime identities; web has bucket objectViewer, Job has bucket objectUser plus project aiplatform.user, and neither has a broad project role. The verifier user has the explicitly approved service-level run.invoker binding; no public member exists and final direct unauthenticated verification returned 403.

Filtered structured logs contain one start, 18 case completions, and one evaluation completion for each run, with no prompt, raw output/evidence, credential, or token fields. Authenticated API and browser verification confirmed baseline publication, exact source commit and fingerprint, desktop/narrow layout, 20 rapid transitions, XART-04's five selectable withheld records with no evidence exposure, and keyboard table scroll. Q1 is not exposed by the UI.

## V4 completion status

V4 is complete and published. The implementation freeze is `ecr-poc-v4-freeze` at `7b76bfaa74d743d3200421d0dad681d740f1ca1c`; v2/v3 tags and all earlier GCS objects remain unchanged. Revision `ecr-poc-00007-xvc` and Job `ecr-poc-evaluate` use the same immutable image digest `sha256:050ff3602378eb43e0fda6046bc35c788a5e891252c97589c346053d425f0a49`.

- Execution: `ecr-poc-evaluate-sxjnm`
- Run: `cloud-v4-20260820T050914Z-92f72d97`
- Result: `runs/cloud-v4-20260820T050914Z-92f72d97/evaluation.json`
- Generation: `1787202918502625`
- SHA-256: `22b07011b48daec60422a91c69420cdf08a58a85e972f51291de7980d0ee3116`
- Published pointer updated: `2026-08-20T05:15:48.851107Z`
- Result: 18/18 cases, zero role errors, metrics and provenance validation passed

Provisioning uploaded 26 immutable objects under `frozen/ecr-poc-v4`. The Job ran as one sequential task with parallelism 1, retries 0, 1 CPU, 1 GiB, and a 1,800-second timeout. Publication followed the terminal checkpoint generation/SHA seal and full v4 identity validation.

Comprehensive verification passed GCS pointer integrity, same service/Job digest, dedicated web/job identities, exact narrow IAM roles, no forbidden broad role, private unauthenticated 403, and structured logs with one start, 18 terminal cases, and one completion without prompt/raw-evidence/credential fields. Deployed browser verification confirmed the v4 run/provenance and representative case values; the independent audit is recorded separately.

## V3 completion status

V3 is a complete, published experiment whose independent UI audit failed final acceptance. The implementation freeze is `ecr-poc-v3-freeze` at `3984e77961b6edeacb2286935f65c1dd13c80a3e`; `ecr-poc-v2-freeze` and all v1/v2 objects remain unchanged. Revision `ecr-poc-00006-6jz` and Job `ecr-poc-evaluate` use the same immutable image digest `sha256:6d0ccf8179655f4211344d7d57403273220e252ac7388b0e7e08787376363c79`.

- Execution: `ecr-poc-evaluate-fq5s4`
- Run: `cloud-v3-20260820T043842Z-6e260831`
- Result: `runs/cloud-v3-20260820T043842Z-6e260831/evaluation.json`
- Generation: `1787201087845537`
- SHA-256: `34ba69003c632d30a93aa47d3e21d4eb166634b1dcd91b44badc1b9de5ef23a1`
- Published pointer updated: `2026-08-20T04:45:11.889647Z`
- Result: 18/18 cases, zero role errors, metrics and provenance validation passed

Provisioning uploaded 25 immutable objects under `frozen/ecr-poc-v3` into the existing hardened bucket. The single billable task ran sequentially with parallelism 1, retries 0, 1 CPU, 1 GiB, and a 1,800-second timeout. Publication occurred only after the checkpoint sealed the evaluation generation/SHA and all source/tag/manifest/execution/image checks passed.

The final Cloud verification confirmed dedicated `ecr-poc-web` and `ecr-poc-job` identities, exact bucket/project roles, no Editor/Owner/Storage Admin on either identity, private unauthenticated 403, one structured `job_started`, 18 `case_completed`, and one `evaluation_completed` for the v3 run, with no prompt/raw-evidence/credential fields. Browser review confirmed the revised cold-start copy but found three major UI defects: stale overlapping responses, Reload wrapping at 390 px, and lost keyboard focus after Reload. V3 remains immutable evidence and is not rewritten to conceal those findings.

## V2 completion status

V2 is complete and published. The final corrective freeze is `ecr-poc-v2-freeze` at `10c59bfba3e1b37afde026548f4c1f51ec6526ed`. Revision `ecr-poc-00005-485` and Job `ecr-poc-evaluate` use the same immutable image digest `sha256:65d65dc7924ca535c4d8c659d13e1297155c83dda993755c83399350a7b164c6`.

- Final execution: `ecr-poc-evaluate-587r6`
- Final run: `cloud-v2-20260820T035505Z-56ad91df`
- Result: `runs/cloud-v2-20260820T035505Z-56ad91df/evaluation.json`
- Generation: `1787198456573991`
- SHA-256: `8ac24782609bcd61f9589f78f9786468ab6badd16e8461298287e4ad2be2ffb0`
- Published pointer updated: `2026-08-20T04:01:19.342489Z`
- Result: 18/18 cases, zero role errors, publication validation passed

The hardened bucket `ecr-poc-912838451352-asia-northeast3` has uniform bucket access, public-access prevention, and versioning. The web identity has bucket `storage.objectViewer`; the Job identity has bucket `storage.objectUser` and project `aiplatform.user`. Neither new identity has Editor, Owner, or Storage Admin. The service remains private and unauthenticated requests return 403.

The first v2 provisioning attempt stopped before service-account, IAM, or upload steps because the installed gcloud release rejected value-form PAP/versioning flags. The corrected retry created the hardened bucket and dedicated identities. A subsequent pre-run inspection caught Job argument serialization and verifier JSON-path defects before a model call; both were fixed and re-frozen.

The first completed v2 run (`cloud-v2-20260820T032620Z-bc550a11`) passed pipeline, GCS, IAM, logging, and private-access validation. An independent browser audit then rejected its provenance presentation because the visible run ID was ambiguously truncated and the footer said `legacy freeze`. That immutable result remains historical. The UI was corrected, committed and tagged before the final redeploy and 18-case rerun above.

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
