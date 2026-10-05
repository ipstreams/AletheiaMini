"""Train a provenance-linked Byte-Level BPE tokenizer for an Aletheia corpus build.

Tokenizer training reads only train.jsonl. Validation and test text are read only after
the tokenizer is frozen, to report tokenization behavior without vocabulary leakage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable

from tokenizers import Tokenizer, decoders, models, normalizers, pre_tokenizers, trainers

from validate_corpus import validate

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUILD = PROJECT_ROOT / "data" / "corpus_builds" / "pilot-v0.1-manuscript"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "tokenizers"
SCRIPT_VERSION = "0.1.0"
SPECIAL_TOKENS = ["<pad>", "<unk>", "<bos>", "<eos>", "<doc>"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict) or not isinstance(value.get("text"), str):
            raise ValueError(f"Invalid text record at {path}:{line_number}")
        records.append(value)
    return records


def text_iterator(records: list[dict[str, Any]]) -> Iterable[str]:
    for record in records:
        yield "<doc>\n" + record["text"] + "\n<eos>"


def count_whitespace_tokens(text: str) -> int:
    return len(re.findall(r"\S+", text))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a Byte-Level BPE tokenizer only from an Aletheia corpus build's train split."
    )
    parser.add_argument("--corpus-build", type=Path, default=DEFAULT_BUILD)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--tokenizer-id", default=None)
    parser.add_argument("--vocab-size", type=int, default=16_384)
    parser.add_argument("--min-frequency", type=int, default=2)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--allow-unready-corpus",
        action="store_true",
        help="Permit diagnostic tokenizer training on a corpus that is not training-ready.",
    )
    return parser.parse_args()


def make_validation_args(build: Path, report: Path, allow_unready: bool) -> SimpleNamespace:
    return SimpleNamespace(
        corpus_build=build,
        report=report,
        min_documents_per_split=1,
        min_unique_sources=3,
        min_total_whitespace_tokens=100_000,
        max_single_source_share=0.60,
        allow_unready_corpus=allow_unready,
    )


def split_tokenization_stats(tokenizer: Tokenizer, records: list[dict[str, Any]]) -> dict[str, float | int]:
    unknown_id = tokenizer.token_to_id("<unk>")
    document_count = len(records)
    character_count = 0
    whitespace_token_count = 0
    tokenizer_token_count = 0
    unknown_token_count = 0

    for record in records:
        text = record["text"]
        encoding = tokenizer.encode(text, add_special_tokens=False)
        character_count += len(text)
        whitespace_token_count += count_whitespace_tokens(text)
        tokenizer_token_count += len(encoding.ids)
        if unknown_id is not None:
            unknown_token_count += sum(token_id == unknown_id for token_id in encoding.ids)

    return {
        "document_count": document_count,
        "character_count": character_count,
        "whitespace_token_count": whitespace_token_count,
        "tokenizer_token_count": tokenizer_token_count,
        "tokens_per_character": round(tokenizer_token_count / character_count, 8) if character_count else 0.0,
        "tokens_per_whitespace_token": round(tokenizer_token_count / whitespace_token_count, 8)
        if whitespace_token_count
        else 0.0,
        "unknown_token_count": unknown_token_count,
        "unknown_token_rate": round(unknown_token_count / tokenizer_token_count, 8)
        if tokenizer_token_count
        else 0.0,
    }


def main() -> None:
    args = parse_args()
    if args.vocab_size < len(SPECIAL_TOKENS) + 256:
        raise ValueError(f"vocab-size must be at least {len(SPECIAL_TOKENS) + 256} for byte-level BPE")
    if args.min_frequency < 1:
        raise ValueError("min-frequency must be at least one")

    build = args.corpus_build.resolve()
    build_manifest_path = build / "corpus_build_manifest.json"
    if not build_manifest_path.is_file():
        raise FileNotFoundError(f"Corpus build manifest is missing: {build_manifest_path}")
    build_manifest = read_json(build_manifest_path)
    build_id = str(build_manifest.get("corpus_build_id", "unknown-build"))
    tokenizer_id = args.tokenizer_id or f"{build_id}-bpe-{args.vocab_size}"
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,100}", tokenizer_id):
        raise ValueError("tokenizer-id must use lowercase letters, digits, periods, underscores, or hyphens")

    output_root = args.output_root.resolve()
    target = output_root / tokenizer_id
    temporary = output_root / f".{tokenizer_id}.tmp"
    if target.exists() and not args.force:
        raise FileExistsError(f"Tokenizer output exists: {target}; use --force to replace it")
    if temporary.exists():
        shutil.rmtree(temporary)
    if target.exists() and args.force:
        shutil.rmtree(target)

    validation_report_path = temporary / "corpus_validation_report.json"
    temporary.mkdir(parents=True, exist_ok=False)
    validation_report = validate(
        make_validation_args(build, validation_report_path, args.allow_unready_corpus)
    )
    if not validation_report["passed"]:
        shutil.rmtree(temporary)
        raise ValueError(
            "Corpus validation failed. Resolve errors before tokenizer training, or use "
            "--allow-unready-corpus only for diagnostic size/split warnings."
        )

    train_path = build / "train.jsonl"
    validation_path = build / "validation.jsonl"
    test_path = build / "test.jsonl"
    train_records = read_jsonl(train_path)
    if not train_records:
        shutil.rmtree(temporary)
        raise ValueError("Training split is empty; tokenizer training cannot proceed")

    tokenizer = Tokenizer(models.BPE(unk_token="<unk>"))
    tokenizer.normalizer = normalizers.NFC()
    tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tokenizer.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(
        vocab_size=args.vocab_size,
        min_frequency=args.min_frequency,
        special_tokens=SPECIAL_TOKENS,
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
    )
    tokenizer.train_from_iterator(text_iterator(train_records), trainer=trainer)
    tokenizer.save(str(temporary / "tokenizer.json"))
    tokenizer.model.save(str(temporary))

    split_stats = {
        "train": split_tokenization_stats(tokenizer, train_records),
        "validation": split_tokenization_stats(tokenizer, read_jsonl(validation_path)),
        "test": split_tokenization_stats(tokenizer, read_jsonl(test_path)),
    }
    tokenizer_manifest = {
        "project": "Aletheia",
        "tokenizer_id": tokenizer_id,
        "script": "src/train_corpus_tokenizer.py",
        "script_version": SCRIPT_VERSION,
        "trained_utc": datetime.now(UTC).isoformat(),
        "tokenizer_type": "Byte-Level BPE",
        "requested_vocab_size": args.vocab_size,
        "actual_vocab_size": tokenizer.get_vocab_size(),
        "min_frequency": args.min_frequency,
        "special_tokens": SPECIAL_TOKENS,
        "corpus_build_id": build_id,
        "corpus_build_manifest_sha256": sha256_file(build_manifest_path),
        "train_jsonl_sha256": sha256_file(train_path),
        "validation_jsonl_sha256": sha256_file(validation_path),
        "test_jsonl_sha256": sha256_file(test_path),
        "trained_on_split": "train",
        "allow_unready_corpus": args.allow_unready_corpus,
        "corpus_validation_passed": validation_report["passed"],
        "corpus_validation_error_count": len(validation_report["errors"]),
        "corpus_validation_warning_count": len(validation_report["warnings"]),
        "partition_tokenization_statistics": split_stats,
    }
    (temporary / "tokenizer_manifest.json").write_text(
        json.dumps(tokenizer_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    print(
        json.dumps(
            {
                "tokenizer_id": tokenizer_id,
                "actual_vocab_size": tokenizer.get_vocab_size(),
                "output": str(target),
                "trained_on_split": "train",
                "corpus_validation_warning_count": len(validation_report["warnings"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, FileExistsError, ValueError, json.JSONDecodeError) as error:
        print(f"Tokenizer training failed: {error}", file=sys.stderr)
        raise SystemExit(2) from error
