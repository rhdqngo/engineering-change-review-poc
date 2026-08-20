from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path

import uvicorn

from .data import (
    DEFAULT_EXPERIMENT_MANIFEST,
    validate_all,
    validate_historical_versions,
)
from .embedding_index import write_embedding_index
from .evaluation import evaluate
from .identifier_index import write_identifier_index
from .ingest import write_corpus
from .quality import write_comparison
from .retrieval import DeterministicHashEmbedder, VertexEmbedder
from .storage import (
    GcsRunStore,
    load_published_run,
    materialize_gcs_prefix,
    publish_run,
    seed_historical_pointer,
    upload_frozen_tree,
    v6_freeze_payload_relatives,
    validate_historical_runs,
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
    subcommands.add_parser(
        "validate-historical",
        help="offline-only validation of immutable v1-v5 data and manifests",
    )
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
    comparison = subcommands.add_parser(
        "compare-results", help="classify and compare a frozen baseline and one-variable variant"
    )
    comparison.add_argument("--baseline", type=Path, required=True)
    comparison.add_argument("--variant", type=Path, required=True)
    comparison.add_argument("--output", type=Path, required=True)
    evaluation.add_argument("--cloud-execution")
    evaluation.add_argument("--container-image-digest")
    evaluation.add_argument(
        "--no-update-latest",
        action="store_true",
        help="write the named result without changing results/latest.json",
    )
    cloud_evaluation = subcommands.add_parser(
        "cloud-evaluate", help="run a frozen versioned experiment from and to GCS"
    )
    cloud_evaluation.add_argument("--provider", default="vertex-adk")
    cloud_evaluation.add_argument("--embedding", default="vertex")
    cloud_evaluation.add_argument(
        "--experiment-manifest",
        default=os.environ.get("ECR_EXPERIMENT_MANIFEST", DEFAULT_EXPERIMENT_MANIFEST),
    )
    upload_freeze = subcommands.add_parser(
        "upload-freeze", help="immutably upload frozen inputs to GCS"
    )
    upload_freeze.add_argument("--bucket", required=True)
    upload_freeze.add_argument("--prefix", default="frozen/ecr-poc-v6")
    upload_freeze.add_argument("--root", type=Path, default=Path.cwd())
    upload_freeze.add_argument(
        "--payload-only",
        action="store_true",
        help="upload only the five v6 payload objects needed before the Git freeze",
    )
    upload_freeze.add_argument(
        "--inventory-output",
        type=Path,
        help="write the returned generation/SHA inventory to a local JSON file",
    )
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
    publish.add_argument("--run-prefix", default="runs/v6")
    publish.add_argument("--published-object", default="published/v6/demo.json")
    verify = subcommands.add_parser(
        "verify-published", help="validate the published GCS evaluation pointer"
    )
    verify.add_argument("--bucket", required=True)
    verify.add_argument("--published-object", default="published/v6/demo.json")
    serve = subcommands.add_parser("serve", help="run the Demo UI/API")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    ingest = subcommands.add_parser(
        "ingest-cfs", help="deterministically ingest an official recursive cFS checkout"
    )
    ingest.add_argument("--source", type=Path, required=True)
    ingest.add_argument("--output-root", type=Path, required=True)
    stage = subcommands.add_parser(
        "stage-v6-inputs", help="stage tracked v6 cases, prompt, and manifest into a data root"
    )
    stage.add_argument("--output-root", type=Path, required=True)
    index = subcommands.add_parser(
        "build-index", help="create an immutable row-major document embedding index"
    )
    index.add_argument("--data-root", type=Path, required=True)
    index.add_argument("--provider", choices=["local", "vertex"], required=True)
    index.add_argument("--dimensions", type=int)
    index.add_argument(
        "--cache-path",
        type=Path,
        help="local resumable hash/vector cache used only while building a Vertex index",
    )
    identifier_index = subcommands.add_parser(
        "build-identifier-index",
        help="create the deterministic typed one-hop identifier index",
    )
    identifier_index.add_argument("--data-root", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "validate-data":
        print(json.dumps(validate_all(), indent=2))
        return
    if args.command == "ingest-cfs":
        print(json.dumps(write_corpus(args.source, args.output_root), indent=2))
        return
    if args.command == "stage-v6-inputs":
        root = Path.cwd()
        staged: list[str] = []
        for relative in (
            "data/cases/cases-v6.json",
            "data/prompts/ecr-poc-v6.json",
            "data/experiments/ecr-poc-v6.json",
            "docs/plans/LLM 기반 우주 Engineering Change Review.md",
        ):
            source = root / relative
            destination = args.output_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            staged.append(relative)
        print(json.dumps({"staged": staged}, indent=2))
        return
    if args.command == "build-identifier-index":
        from .data import load_artifacts, load_experiment_manifest, sha256_file

        manifest = load_experiment_manifest(args.data_root, DEFAULT_EXPERIMENT_MANIFEST)
        artifacts = load_artifacts(args.data_root, DEFAULT_EXPERIMENT_MANIFEST)
        package_path = args.data_root / str(manifest["artifact_package_file"])
        destination = args.data_root / str(manifest["identifier_index_file"])
        print(
            json.dumps(
                write_identifier_index(
                    destination,
                    artifacts,
                    sha256_file(package_path),
                ),
                indent=2,
            )
        )
        return
    if args.command == "build-index":
        from .data import load_artifacts, load_experiment_manifest, sha256_file

        manifest = load_experiment_manifest(args.data_root, DEFAULT_EXPERIMENT_MANIFEST)
        artifacts = load_artifacts(args.data_root, DEFAULT_EXPERIMENT_MANIFEST)
        if args.provider == "vertex":
            project = os.environ.get("GOOGLE_CLOUD_PROJECT")
            if not project:
                raise SystemExit("GOOGLE_CLOUD_PROJECT is required for Vertex embeddings")
            dimensions = args.dimensions or 768
            embedder: VertexEmbedder | DeterministicHashEmbedder = VertexEmbedder(
                project=project,
                location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
                model_name="gemini-embedding-001",
                output_dimensionality=dimensions,
                cache_path=args.cache_path,
            )
        else:
            dimensions = args.dimensions or 384
            embedder = DeterministicHashEmbedder(dimensions)
        package_path = args.data_root / str(manifest["artifact_package_file"])
        metadata = write_embedding_index(
            artifacts,
            embedder,
            args.data_root,
            experiment_id=str(manifest["experiment_id"]),
            dimensions=dimensions,
            artifact_package_sha256=sha256_file(package_path),
        )
        print(json.dumps(metadata, indent=2))
        return
    if args.command == "validate-historical":
        print(
            json.dumps(
                {
                    "data": validate_historical_versions(),
                    "runs": validate_historical_runs(),
                },
                indent=2,
            )
        )
        return
    if args.command == "compare-results":
        print(
            json.dumps(
                write_comparison(args.baseline, args.variant, args.output),
                indent=2,
            )
        )
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
                    update_latest=not args.no_update_latest,
                )
            )
        print(json.dumps(run.metrics, indent=2))
        return
    if args.command == "cloud-evaluate":
        bucket = os.environ["ECR_GCS_BUCKET"]
        run_id = os.environ["ECR_RUN_ID"]
        source_commit = os.environ["ECR_SOURCE_COMMIT"]
        input_prefix = os.environ.get("ECR_GCS_INPUT_PREFIX", "frozen/ecr-poc-v6")
        with tempfile.TemporaryDirectory(prefix="ecr-poc-input-") as temporary:
            root = Path(temporary)
            materialize_gcs_prefix(bucket, input_prefix, root)
            store = GcsRunStore(
                bucket,
                run_id,
                prefix=os.environ.get("ECR_GCS_RUN_PREFIX", "runs/v6"),
            )
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
        relatives = (
            v6_freeze_payload_relatives(args.root) if args.payload_only else None
        )
        inventory = upload_frozen_tree(
            args.root,
            args.bucket,
            args.prefix,
            only_relatives=relatives,
        )
        if args.inventory_output is not None:
            args.inventory_output.parent.mkdir(parents=True, exist_ok=True)
            args.inventory_output.write_text(
                json.dumps(inventory, indent=2) + "\n", encoding="utf-8"
            )
        print(json.dumps(inventory, indent=2))
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
                run_prefix=args.run_prefix,
                published_object_name=args.published_object,
            ).model_dump_json(indent=2)
        )
        return
    if args.command == "verify-published":
        run, pointer = load_published_run(args.bucket, args.published_object)
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
