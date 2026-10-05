"""Validate an Aletheia corpus build before tokenizer training or model pretraining.

The validator reads corpus artifacts produced by build_pilot_corpus.py. It reports
provenance and distribution metrics, and exits non-zero when hard integrity or
readiness requirements fail.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUILD = PROJECT_ROOT / "data" / "corpus_builds" / "pilot-v0.1-manuscript"
REQUIRED_DOCUMENT_FIELDS = {
    "document_id",
    "source_id",
    "split",
    "normalized_sha256",
    "source_sha256",
    "rights_basis",
    "content_domain",
    "epistemic_status",
    "human_or_model_origin",
    "sensitivity_tags",
    "text",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot parse JSON file {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ValueError(f"Cannot read JSONL file {path}: {error}") from error
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON at {path}:{line_number}: {error.msg}") from error
        if not isinstance(record, dict):
            raise ValueError(f"Expected JSON object at {path}:{line_number}")
        records.append(record)
    return records


def count_tokens(text: str) -> int:
    return len(re.findall(r"\S+", text))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an Aletheia corpus build.")
    parser.add_argument("--corpus-build", type=Path, default=DEFAULT_BUILD)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--min-documents-per-split", type=int, default=1)
    parser.add_argument("--min-unique-sources", type=int, default=3)
    parser.add_argument("--min-total-whitespace-tokens", type=int, default=100_000)
    parser.add_argument("--max-single-source-share", type=float, default=0.60)
    parser.add_argument(
        "--allow-unready-corpus",
        action="store_true",
        help="Downgrade corpus-size and split-readiness failures to warnings for diagnostics only.",
    )
    return parser.parse_args()


def add_readiness_finding(
    report: dict[str, Any],
    message: str,
    allow_unready: bool,
) -> None:
    target = report["warnings"] if allow_unready else report["errors"]
    target.append(message)


def validate(args: argparse.Namespace) -> dict[str, Any]:
    build = args.corpus_build.resolve()
    report_path = args.report.resolve() if args.report else build / "validation_report.json"
    report: dict[str, Any] = {
        "project": "Aletheia",
        "validator": "src/validate_corpus.py",
        "validator_version": "0.1.0",
        "validated_utc": datetime.now(UTC).isoformat(),
        "corpus_build_path": str(build),
        "errors": [],
        "warnings": [],
        "metrics": {},
    }
    required_files = {
        "build_manifest": build / "corpus_build_manifest.json",
        "corpus": build / "corpus.jsonl",
        "train": build / "train.jsonl",
        "validation": build / "validation.jsonl",
        "test": build / "test.jsonl",
        "accepted_sources": build / "accepted_sources.jsonl",
        "excluded_sources": build / "excluded_sources.jsonl",
    }
    missing = [name for name, path in required_files.items() if not path.is_file()]
    if missing:
        report["errors"].append("Missing required build files: " + ", ".join(missing))
        report["passed"] = False
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report

    try:
        build_manifest = read_json(required_files["build_manifest"])
        corpus = read_jsonl(required_files["corpus"])
        split_records = {
            split: read_jsonl(path)
            for split, path in (("train", required_files["train"]), ("validation", required_files["validation"]), ("test", required_files["test"]))
        }
        accepted_sources = read_jsonl(required_files["accepted_sources"])
        excluded_sources = read_jsonl(required_files["excluded_sources"])
    except ValueError as error:
        report["errors"].append(str(error))
        report["passed"] = False
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report

    report["metrics"]["file_sha256"] = {
        name: sha256_file(path) for name, path in required_files.items()
    }
    report["metrics"]["build_id"] = build_manifest.get("corpus_build_id")
    report["metrics"]["declared_training_ready"] = build_manifest.get("training_ready")
    report["metrics"]["declared_missing_splits"] = build_manifest.get("missing_splits", [])

    document_ids: set[str] = set()
    normalized_hashes: dict[str, set[str]] = defaultdict(set)
    source_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    epistemic_counts: Counter[str] = Counter()
    origin_counts: Counter[str] = Counter()
    sensitivity_counts: Counter[str] = Counter()
    total_characters = 0
    total_tokens = 0

    for index, document in enumerate(corpus, start=1):
        missing_fields = sorted(REQUIRED_DOCUMENT_FIELDS - document.keys())
        if missing_fields:
            report["errors"].append(
                f"corpus.jsonl record {index} missing fields: {', '.join(missing_fields)}"
            )
            continue
        document_id = document["document_id"]
        if document_id in document_ids:
            report["errors"].append(f"Duplicate document_id in corpus.jsonl: {document_id}")
        document_ids.add(document_id)
        normalized_hashes[str(document["normalized_sha256"])].add(str(document["split"]))
        source_counts[str(document["source_id"])] += 1
        domain_counts[str(document["content_domain"])] += 1
        epistemic_counts[str(document["epistemic_status"])] += 1
        origin_counts[str(document["human_or_model_origin"])] += 1
        for tag in document["sensitivity_tags"]:
            sensitivity_counts[str(tag)] += 1
        text = document["text"]
        if not isinstance(text, str) or not text.strip():
            report["errors"].append(f"Empty or invalid text for document {document_id}")
        else:
            total_characters += len(text)
            total_tokens += count_tokens(text)

    for normalized_hash, splits in normalized_hashes.items():
        if len(splits) > 1:
            report["errors"].append(
                f"Normalized-content hash appears in more than one split: {normalized_hash}"
            )

    split_id_sets: dict[str, set[str]] = {}
    for split, records in split_records.items():
        split_ids: set[str] = set()
        for record in records:
            if record.get("split") != split:
                report["errors"].append(
                    f"Document {record.get('document_id', '?')} is stored in {split}.jsonl but declares split={record.get('split')}"
                )
            document_id = record.get("document_id")
            if document_id in split_ids:
                report["errors"].append(f"Duplicate document_id in {split}.jsonl: {document_id}")
            split_ids.add(document_id)
        split_id_sets[split] = split_ids

    union_ids = set().union(*split_id_sets.values())
    if union_ids != document_ids:
        report["errors"].append("The union of split document IDs does not match corpus.jsonl")
    intersections = [
        (left, right, split_id_sets[left].intersection(split_id_sets[right]))
        for left, right in (("train", "validation"), ("train", "test"), ("validation", "test"))
    ]
    for left, right, overlap in intersections:
        if overlap:
            report["errors"].append(
                f"Split overlap between {left} and {right}: {', '.join(sorted(overlap))}"
            )

    declared_document_count = build_manifest.get("document_count")
    if declared_document_count != len(corpus):
        report["errors"].append(
            f"Build manifest document_count={declared_document_count} but corpus contains {len(corpus)} documents"
        )
    declared_split_counts = build_manifest.get("split_counts", {})
    observed_split_counts = {split: len(records) for split, records in split_records.items()}
    if declared_split_counts != observed_split_counts:
        report["errors"].append(
            f"Build manifest split_counts={declared_split_counts} but observed counts={observed_split_counts}"
        )

    accepted_source_ids = {str(record.get("source_id")) for record in accepted_sources}
    corpus_source_ids = set(source_counts)
    untracked_sources = corpus_source_ids - accepted_source_ids
    if untracked_sources:
        report["errors"].append(
            "Corpus documents have no matching accepted-source record: " + ", ".join(sorted(untracked_sources))
        )
    for source in accepted_sources:
        if not (
            source.get("training_use_approved")
            and source.get("review_status") == "approved"
            and source.get("include_in_pilot")
            and source.get("privacy_review") in {"passed", "not_required"}
        ):
            report["errors"].append(
                f"Accepted source fails eligibility gate: {source.get('source_id', '?')}"
            )

    for split, count in observed_split_counts.items():
        if count < args.min_documents_per_split:
            add_readiness_finding(
                report,
                f"Split {split} contains {count} documents; minimum is {args.min_documents_per_split}",
                args.allow_unready_corpus,
            )
    if len(corpus_source_ids) < args.min_unique_sources:
        add_readiness_finding(
            report,
            f"Corpus contains {len(corpus_source_ids)} unique sources; minimum is {args.min_unique_sources}",
            args.allow_unready_corpus,
        )
    if total_tokens < args.min_total_whitespace_tokens:
        add_readiness_finding(
            report,
            f"Corpus contains {total_tokens} whitespace tokens; minimum is {args.min_total_whitespace_tokens}",
            args.allow_unready_corpus,
        )
    if corpus:
        largest_source, largest_count = source_counts.most_common(1)[0]
        largest_share = largest_count / len(corpus)
        if largest_share > args.max_single_source_share:
            add_readiness_finding(
                report,
                f"Source {largest_source} contributes {largest_share:.1%} of documents; maximum is {args.max_single_source_share:.1%}",
                args.allow_unready_corpus,
            )

    report["metrics"].update(
        {
            "document_count": len(corpus),
            "unique_source_count": len(corpus_source_ids),
            "split_counts": observed_split_counts,
            "total_characters": total_characters,
            "approximate_whitespace_token_count": total_tokens,
            "domain_counts": dict(sorted(domain_counts.items())),
            "epistemic_status_counts": dict(sorted(epistemic_counts.items())),
            "origin_counts": dict(sorted(origin_counts.items())),
            "sensitivity_tag_counts": dict(sorted(sensitivity_counts.items())),
            "accepted_source_count": len(accepted_sources),
            "excluded_source_count": len(excluded_sources),
        }
    )
    report["passed"] = not report["errors"]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    args = parse_args()
    if args.min_documents_per_split < 1 or args.min_unique_sources < 1:
        raise ValueError("Minimum document and source thresholds must be at least one")
    if args.min_total_whitespace_tokens < 1:
        raise ValueError("Minimum token threshold must be at least one")
    if not 0 < args.max_single_source_share <= 1:
        raise ValueError("max-single-source-share must be within (0, 1]")

    report = validate(args)
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "error_count": len(report["errors"]),
                "warning_count": len(report["warnings"]),
                "report": str((args.report or args.corpus_build / "validation_report.json").resolve()),
            },
            indent=2,
        )
    )
    if not report["passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(f"Corpus validation failed: {error}", file=sys.stderr)
        raise SystemExit(2) from error
