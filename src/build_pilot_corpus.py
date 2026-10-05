"""Build an approval-gated, traceable pilot corpus for Aletheia.

This script intentionally accepts only manifest-approved local text sources. It does not
crawl the web, infer rights, or bypass privacy review. Each emitted document retains its
source identity, content hash, epistemic status, and sensitivity labels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT_ROOT / "corpus" / "pilot_sources.jsonl"
DEFAULT_BUILD_ROOT = PROJECT_ROOT / "data" / "corpus_builds"
SCRIPT_VERSION = "0.1.0"

REQUIRED_FIELDS = {
    "source_id",
    "title",
    "source_path",
    "source_type",
    "rights_basis",
    "content_domain",
    "epistemic_status",
    "human_or_model_origin",
    "sensitivity_tags",
    "privacy_review",
    "training_use_approved",
    "review_status",
    "include_in_pilot",
}
VALID_SOURCE_TYPES = {
    "first_party",
    "public_domain",
    "open_license",
    "permissioned",
    "official_documentation",
    "model_output",
}
VALID_DOMAINS = {
    "aletheia_first_party",
    "philosophy_ethics_epistemology",
    "literary_reflection",
    "ai_cognitive_science",
    "scientific_methodology",
    "curated_dialogue",
}
VALID_EPISTEMIC_STATUSES = {
    "narrative",
    "record",
    "hypothesis",
    "technical_explanation",
    "test_protocol",
    "opinion",
    "metaphor",
    "unverified_claim",
    "mixed",
}
VALID_REVIEW_STATUSES = {"approved", "quarantined", "rejected"}
VALID_PRIVACY_STATUSES = {"not_required", "pending", "passed", "failed"}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an approval-gated Aletheia pilot corpus from a JSONL source manifest."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--build-id", default="pilot-v0.1")
    parser.add_argument("--build-root", type=Path, default=DEFAULT_BUILD_ROOT)
    parser.add_argument("--force", action="store_true", help="Replace an existing build directory.")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs without writing output.")
    parser.add_argument(
        "--allow-incomplete-splits",
        action="store_true",
        help="Allow a diagnostic build with an empty train, validation, or test split.",
    )
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Source manifest does not exist: {path}")
    records: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON at {path}:{number}: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"Manifest line {number} must be a JSON object")
        value["_manifest_line"] = number
        records.append(value)
    if not records:
        raise ValueError("Source manifest contains no usable records")
    return records


def validate_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - record.keys())
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
    if record.get("source_type") not in VALID_SOURCE_TYPES:
        errors.append("invalid source_type")
    if record.get("content_domain") not in VALID_DOMAINS:
        errors.append("invalid content_domain")
    if record.get("epistemic_status") not in VALID_EPISTEMIC_STATUSES:
        errors.append("invalid epistemic_status")
    if record.get("review_status") not in VALID_REVIEW_STATUSES:
        errors.append("invalid review_status")
    if record.get("privacy_review") not in VALID_PRIVACY_STATUSES:
        errors.append("invalid privacy_review")
    if not isinstance(record.get("training_use_approved"), bool):
        errors.append("training_use_approved must be boolean")
    if not isinstance(record.get("include_in_pilot"), bool):
        errors.append("include_in_pilot must be boolean")
    if not isinstance(record.get("sensitivity_tags"), list):
        errors.append("sensitivity_tags must be a list")
    source_id = record.get("source_id")
    if not isinstance(source_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,80}", source_id):
        errors.append("source_id must use lowercase letters, digits, underscores, or hyphens")
    return errors


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_project_path(raw_path: str) -> Path:
    candidate = (PROJECT_ROOT / raw_path).resolve()
    if not is_relative_to(candidate, PROJECT_ROOT):
        raise ValueError("source_path must resolve inside the Aletheia project directory")
    return candidate


def normalize_text(raw: bytes) -> tuple[str, int]:
    text = raw.decode("utf-8", errors="replace")
    replacement_count = text.count("\ufffd")
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(character if (character >= " " or character in "\n\t") else " " for character in text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip(), replacement_count


def choose_split(document_id: str) -> str:
    bucket = int(hashlib.sha256(document_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "validation"
    return "test"


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as destination:
        for record in records:
            destination.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def build_document(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    source_path = resolve_project_path(str(record["source_path"]))
    if not source_path.is_file():
        raise FileNotFoundError(f"Approved source is missing: {source_path}")

    raw = source_path.read_bytes()
    observed_source_hash = sha256_bytes(raw)
    declared_source_hash = record.get("source_sha256")
    if declared_source_hash and declared_source_hash != observed_source_hash:
        raise ValueError(
            f"Source hash mismatch for {record['source_id']}: expected {declared_source_hash}, "
            f"observed {observed_source_hash}"
        )
    normalized, replacement_count = normalize_text(raw)
    if len(normalized) < 300:
        raise ValueError(f"Source {record['source_id']} has fewer than 300 normalized characters")

    normalized_hash = sha256_bytes(normalized.encode("utf-8"))
    document_id = f"{record['source_id']}--{normalized_hash[:16]}"
    split = choose_split(document_id)
    document = {
        "document_id": document_id,
        "source_id": record["source_id"],
        "title": record["title"],
        "split": split,
        "source_sha256": observed_source_hash,
        "normalized_sha256": normalized_hash,
        "source_type": record["source_type"],
        "rights_basis": record["rights_basis"],
        "content_domain": record["content_domain"],
        "epistemic_status": record["epistemic_status"],
        "human_or_model_origin": record["human_or_model_origin"],
        "sensitivity_tags": record["sensitivity_tags"],
        "normalization": {"unicode": "NFC", "replacement_characters": replacement_count},
        "text": normalized,
    }
    resolved_record = {
        key: value for key, value in record.items() if not key.startswith("_")
    }
    resolved_record["observed_source_sha256"] = observed_source_hash
    resolved_record["normalized_sha256"] = normalized_hash
    resolved_record["emitted_document_id"] = document_id
    resolved_record["assigned_split"] = split
    return document, resolved_record


def main() -> None:
    args = parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,80}", args.build_id):
        raise ValueError("build-id must use lowercase letters, digits, periods, underscores, or hyphens")

    manifest_path = args.manifest.resolve()
    records = load_jsonl(manifest_path)
    source_ids: set[str] = set()
    approved: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []

    for record in records:
        line = record["_manifest_line"]
        errors = validate_record(record)
        if record.get("source_id") in source_ids:
            errors.append("duplicate source_id")
        source_ids.add(record.get("source_id", ""))
        if errors:
            raise ValueError(f"Manifest line {line} ({record.get('source_id', '?')}): {'; '.join(errors)}")

        eligible = (
            record["training_use_approved"]
            and record["review_status"] == "approved"
            and record["include_in_pilot"]
            and record["privacy_review"] in {"passed", "not_required"}
        )
        if eligible:
            approved.append(record)
        else:
            excluded.append(
                {
                    "source_id": record["source_id"],
                    "manifest_line": line,
                    "decision": "excluded_before_ingestion",
                    "reason": {
                        "training_use_approved": record["training_use_approved"],
                        "review_status": record["review_status"],
                        "include_in_pilot": record["include_in_pilot"],
                        "privacy_review": record["privacy_review"],
                    },
                }
            )

    if not approved:
        raise ValueError("No source record is eligible for ingestion; approve at least one reviewed source")

    documents: list[dict[str, Any]] = []
    resolved_sources: list[dict[str, Any]] = []
    normalized_hashes: set[str] = set()
    for record in approved:
        document, resolved_record = build_document(record)
        if document["normalized_sha256"] in normalized_hashes:
            excluded.append(
                {
                    "source_id": record["source_id"],
                    "decision": "excluded_duplicate_normalized_content",
                    "normalized_sha256": document["normalized_sha256"],
                }
            )
            continue
        normalized_hashes.add(document["normalized_sha256"])
        documents.append(document)
        resolved_sources.append(resolved_record)

    if not documents:
        raise ValueError("No unique documents remained after normalization and deduplication")

    documents.sort(key=lambda document: document["document_id"])
    split_records = {split: [document for document in documents if document["split"] == split] for split in ("train", "validation", "test")}
    missing_splits = [split for split, rows in split_records.items() if not rows]
    if missing_splits and not args.allow_incomplete_splits:
        raise ValueError(
            "Corpus build is not training-ready because these splits are empty: "
            + ", ".join(missing_splits)
            + ". Add more approved sources or use --allow-incomplete-splits only for diagnostics."
        )
    token_estimate = sum(len(re.findall(r"\S+", document["text"])) for document in documents)
    summary = {
        "project": "Aletheia",
        "corpus_build_id": args.build_id,
        "script": "src/build_pilot_corpus.py",
        "script_version": SCRIPT_VERSION,
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "build_created_utc": datetime.now(UTC).isoformat(),
        "document_count": len(documents),
        "split_counts": {split: len(records) for split, records in split_records.items()},
        "missing_splits": missing_splits,
        "training_ready": not missing_splits,
        "approximate_whitespace_token_count": token_estimate,
        "accepted_sources": resolved_sources,
        "excluded_sources": excluded,
    }

    print(
        json.dumps(
            {
                key: summary[key]
                for key in (
                    "corpus_build_id",
                    "document_count",
                    "split_counts",
                    "missing_splits",
                    "training_ready",
                    "approximate_whitespace_token_count",
                )
            },
            indent=2,
        )
    )
    if args.dry_run:
        print("Dry run complete: no corpus files were written.")
        return

    build_root = args.build_root.resolve()
    target = build_root / args.build_id
    temporary = build_root / f".{args.build_id}.tmp"
    if target.exists() and not args.force:
        raise FileExistsError(f"Build directory exists: {target}; use --force to replace it")
    if temporary.exists():
        shutil.rmtree(temporary)
    if target.exists() and args.force:
        shutil.rmtree(target)
    temporary.mkdir(parents=True, exist_ok=False)

    write_jsonl(temporary / "corpus.jsonl", documents)
    for split, rows in split_records.items():
        write_jsonl(temporary / f"{split}.jsonl", rows)
    write_jsonl(temporary / "accepted_sources.jsonl", resolved_sources)
    write_jsonl(temporary / "excluded_sources.jsonl", excluded)
    (temporary / "corpus_build_manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    print(f"Wrote corpus build to {target}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, FileExistsError, ValueError) as error:
        print(f"Corpus build failed: {error}", file=sys.stderr)
        raise SystemExit(2) from error
