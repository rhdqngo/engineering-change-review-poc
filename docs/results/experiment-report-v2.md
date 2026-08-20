# Engineering Change Review Cloud Experiment v2

status: corrective-rerun-pending

The first remotely frozen v2 run completed all 18 cases and passed pipeline, storage, IAM, logging, and publication checks. Independent UI audit then found a major provenance presentation defect: the run ID was ambiguously truncated and the v2 footer said `legacy freeze`. That immutable run remains in GCS, but is not designated as the final accepted result. This report will be populated after the corrected UI is frozen remotely and a new validated 18-case Job run is published.

The final report will record the remote freeze commit and tag, Cloud Run execution and image digest, GCS object generation and SHA-256, actual type-level metrics, structured-log validation, IAM validation, browser evidence, limitations, and an explicit comparison with the retained v1 result.
