from __future__ import annotations

import argparse
import asyncio
import json
import os
import tempfile
from pathlib import Path

import uvicorn

from .data import validate_all
from .evaluation import evaluate
from .storage import (
    GcsRunStore,
    load_published_run,
    materialize_gcs_prefix,
    publish_run,
    seed_historical_pointer,
    upload_frozen_tree,
)


def _parse_gs_uri(uri: str) -> tuple[str, str]:
    if not uri.startswith("gs://"):
        raise ValueError(f"GCS URI must start with gs://: {uri}")
    bucket, separator, prefix = uri[5:].partition("/")
    if not bucket or not separator or not prefix.strip("/"):
        raise ValueError(f"GCS URI must include a bucket and prefix: {uri}")
    return bucket, prefix.strip("/")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ecr-poc",
        description="Evidence-grounded NASA cFS engineering change review PoC",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("validate-data", help="verify frozen cases and NASA source hashes")
    evaluation = subcommands.add_parser("evaluate", help="run all pre-registered cases")
    evaluation.add_argument("--provider", choices=["fixture", "vertex-adk"], required=True)
    evaluation.add_argument("--embedding", choices=["local", "vertex"], required=True)
    evaluation.add_argument("--output", type=Path)
    evaluation.add_argument("--inject-unsupported", action="store_true")
    evaluation.add_argument("--experiment-manifest")
    evaluation.add_argument("--run-id")
    evaluation.add_argument("--source-commit")
    evaluation.add_argument("--gcs-input-uri")
    evaluation.add_argument(
        "--gcs-output-uri", help="GCS run-parent prefix, for example gs://bucket/runs"
    )
    evaluation.add_argument("--cloud-execution")
    evaluation.add_argument("--container-image-digest")
    cloud_evaluation = subcommands.add_parser(
        "cloud-evaluate", help="run a frozen versioned experiment from and to GCS"
    )
    cloud_evaluation.add_argument("--provider", default="vertex-adk")
    cloud_evaluation.add_argument("--embedding", default="vertex")
    cloud_evaluation.add_argument(
        "--experiment-manifest",
        default=os.environ.get("ECR_EXPERIMENT_MANIFEST", "ecr-poc-v3.json"),
    )
    upload_freeze = subcommands.add_parser(
        "upload-freeze", help="immutably upload frozen inputs to GCS"
    )
    upload_freeze.add_argument("--bucket", required=True)
    upload_freeze.add_argument("--prefix", default="frozen/ecr-poc-v3")
    upload_history = subcommands.add_parser(
        "upload-historical", help="immutably upload the retained v1 result to GCS"
    )
    upload_history.add_argument("--bucket", required=True)
    upload_history.add_argument(
        "--source-commit",
        default="c0dd0cc12f1070f5044fc17ee116a2311a9cbddb",
    )
    publish = subcommands.add_parser(
        "publish-run", help="validate and publish one completed GCS evaluation"
    )
    publish.add_argument("--bucket", required=True)
    publish.add_argument("--run-id", required=True)
    publish.add_argument("--source-commit", required=True)
    publish.add_argument("--experiment-manifest", required=True)
    verify = subcommands.add_parser(
        "verify-published", help="validate the published GCS evaluation pointer"
    )
    verify.add_argument("--bucket", required=True)
    serve = subcommands.add_parser("serve", help="run the Demo UI/API")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "validate-data":
        print(json.dumps(validate_all(), indent=2))
        return
    if args.command == "evaluate":
        if bool(args.gcs_input_uri) != bool(args.gcs_output_uri):
            raise SystemExit("--gcs-input-uri and --gcs-output-uri must be supplied together")
        if args.gcs_input_uri:
            if args.output is not None or not args.run_id:
                raise SystemExit("GCS evaluation requires --run-id and forbids --output")
            input_bucket, input_prefix = _parse_gs_uri(args.gcs_input_uri)
            output_bucket, output_prefix = _parse_gs_uri(args.gcs_output_uri)
            if input_bucket != output_bucket:
                raise SystemExit("GCS input and output must use the same dedicated bucket")
            with tempfile.TemporaryDirectory(prefix="ecr-poc-input-") as temporary:
                root = Path(temporary)
                materialize_gcs_prefix(input_bucket, input_prefix, root)
                run = asyncio.run(
                    evaluate(
                        provider_name=args.provider,
                        embedding_provider=args.embedding,
                        root=root,
                        run_id=args.run_id,
                        run_store=GcsRunStore(
                            output_bucket, args.run_id, prefix=output_prefix
                        ),
                        inject_unsupported=args.inject_unsupported,
                        experiment_manifest=args.experiment_manifest,
                        source_commit=args.source_commit,
                        cloud_execution=args.cloud_execution,
                        container_image_digest=args.container_image_digest,
                    )
                )
        else:
            run = asyncio.run(
                evaluate(
                    provider_name=args.provider,
                    embedding_provider=args.embedding,
                    output_path=args.output,
                    inject_unsupported=args.inject_unsupported,
                    experiment_manifest=args.experiment_manifest,
                    run_id=args.run_id,
                    source_commit=args.source_commit,
                    cloud_execution=args.cloud_execution,
                    container_image_digest=args.container_image_digest,
                )
            )
        print(json.dumps(run.metrics, indent=2))
        return
    if args.command == "cloud-evaluate":
        bucket = os.environ["ECR_GCS_BUCKET"]
        run_id = os.environ["ECR_RUN_ID"]
        source_commit = os.environ["ECR_SOURCE_COMMIT"]
        input_prefix = os.environ.get("ECR_GCS_INPUT_PREFIX", "frozen/ecr-poc-v3")
        with tempfile.TemporaryDirectory(prefix="ecr-poc-input-") as temporary:
            root = Path(temporary)
            materialize_gcs_prefix(bucket, input_prefix, root)
            store = GcsRunStore(bucket, run_id)
            run = asyncio.run(
                evaluate(
                    provider_name=args.provider,
                    embedding_provider=args.embedding,
                    root=root,
                    run_id=run_id,
                    run_store=store,
                    experiment_manifest=args.experiment_manifest,
                    source_commit=source_commit,
                    cloud_execution=(
                        os.environ.get("CLOUD_RUN_EXECUTION")
                        or os.environ.get("ECR_CLOUD_EXECUTION")
                    ),
                    container_image_digest=os.environ.get("ECR_CONTAINER_IMAGE_DIGEST"),
                )
            )
        print(json.dumps(run.metrics, indent=2))
        return
    if args.command == "upload-freeze":
        print(
            json.dumps(
                upload_frozen_tree(Path.cwd(), args.bucket, args.prefix), indent=2
            )
        )
        return
    if args.command == "upload-historical":
        print(
            json.dumps(
                {
                    "published": seed_historical_pointer(
                        Path.cwd(), args.bucket, args.source_commit
                    ).model_dump(mode="json"),
                },
                indent=2,
            )
        )
        return
    if args.command == "publish-run":
        print(
            publish_run(
                args.bucket,
                args.run_id,
                args.source_commit,
                args.experiment_manifest,
            ).model_dump_json(indent=2)
        )
        return
    if args.command == "verify-published":
        run, pointer = load_published_run(args.bucket)
        print(
            json.dumps(
                {
                    "run_id": run.run_id,
                    "experiment_id": run.experiment_id,
                    "provider": run.provider,
                    "model": run.model,
                    "cases": len(run.cases),
                    "pointer": pointer.model_dump(mode="json"),
                },
                indent=2,
            )
        )
        return
    if args.command == "serve":
        uvicorn.run("ecr_poc.web:app", host=args.host, port=args.port)
