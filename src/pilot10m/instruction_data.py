"""Verified supervised dialogue loading for Aletheia instruction tuning."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import torch
from tokenizers import Tokenizer

from pilot10m.data import sha256_file


INSTRUCTION_DATA_DIR = Path(__file__).resolve().parents[2] / "instruction_data" / "aletheia-instruction-tuning-v1"


@dataclass(frozen=True)
class InstructionDataMetadata:
    dataset_id: str
    manifest_sha256: str
    train_sha256: str
    validation_sha256: str
    train_example_count: int
    validation_example_count: int
    held_out_suite_name: str
    held_out_suite_excluded_from_training: bool

    def to_dict(self) -> dict[str, str | int | bool]:
        return asdict(self)


def _declared_checksums(data_dir: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for line in (data_dir / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, name = line.split(maxsplit=1)
        checksums[name] = expected
    return checksums


def _load_records(path: Path, expected_split: str) -> list[dict]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not records:
        raise ValueError(f"Instruction split is empty: {path}")
    seen: set[str] = set()
    for record in records:
        if record.get("split") != expected_split:
            raise ValueError(f"Unexpected split field in {record.get('id')}: {record.get('split')}")
        if record.get("rights") != "original_human_authored_rights_cleared":
            raise ValueError(f"Unapproved rights field in {record.get('id')}")
        if record.get("id") in seen:
            raise ValueError(f"Duplicate instruction ID: {record.get('id')}")
        seen.add(record["id"])
        messages = record.get("messages")
        if not isinstance(messages, list) or len(messages) != 2:
            raise ValueError(f"Expected exactly two messages for {record['id']}")
        if [message.get("role") for message in messages] != ["user", "assistant"]:
            raise ValueError(f"Expected user/assistant ordering for {record['id']}")
        if not all(isinstance(message.get("content"), str) and message["content"].strip() for message in messages):
            raise ValueError(f"Empty instruction message in {record['id']}")
    return records


def load_instruction_dataset(data_dir: Path = INSTRUCTION_DATA_DIR) -> tuple[list[dict], list[dict], InstructionDataMetadata]:
    data_dir = data_dir.resolve()
    required = ["MANIFEST.json", "SHA256SUMS.txt", "train.jsonl", "validation.jsonl"]
    if any(not (data_dir / name).is_file() for name in required):
        raise FileNotFoundError(f"Missing instruction data artifact under {data_dir}")
    manifest = json.loads((data_dir / "MANIFEST.json").read_text(encoding="utf-8"))
    if manifest.get("dataset_id") != "aletheia-instruction-tuning-v1":
        raise ValueError("Unexpected instruction dataset identity")
    policy = manifest.get("held_out_evaluation_policy", {})
    if policy.get("locked_suite") != "aletheia-epistemic-eval-v1":
        raise ValueError("Unexpected held-out evaluation suite identity")
    declared = _declared_checksums(data_dir)
    for name in ["MANIFEST.json", "train.jsonl", "validation.jsonl"]:
        actual = sha256_file(data_dir / name)
        if declared.get(name) != actual:
            raise ValueError(f"Checksum mismatch for instruction data file: {name}")
    train = _load_records(data_dir / "train.jsonl", "train")
    validation = _load_records(data_dir / "validation.jsonl", "validation")
    expected_size = manifest.get("size", {})
    if len(train) != expected_size.get("train") or len(validation) != expected_size.get("validation"):
        raise ValueError("Instruction split counts do not match the manifest")
    if set(record["id"] for record in train).intersection(record["id"] for record in validation):
        raise ValueError("Instruction train/validation ID overlap")
    metadata = InstructionDataMetadata(
        dataset_id=manifest["dataset_id"],
        manifest_sha256=sha256_file(data_dir / "MANIFEST.json"),
        train_sha256=sha256_file(data_dir / "train.jsonl"),
        validation_sha256=sha256_file(data_dir / "validation.jsonl"),
        train_example_count=len(train),
        validation_example_count=len(validation),
        held_out_suite_name=policy["locked_suite"],
        held_out_suite_excluded_from_training=True,
    )
    return train, validation, metadata


def format_supervised_example(record: dict, tokenizer: Tokenizer, context_length: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Return same-length input and target tensors; user-side targets are -100."""
    bos = tokenizer.token_to_id("<bos>")
    eos = tokenizer.token_to_id("<eos>")
    doc = tokenizer.token_to_id("<doc>")
    if None in {bos, eos, doc}:
        raise ValueError("Tokenizer is missing required special tokens")
    user_text = record["messages"][0]["content"]
    assistant_text = record["messages"][1]["content"]
    user_prefix = "User:\n"
    assistant_prefix = "\nAssistant:\n"
    prefix_ids = [int(bos), int(doc)] + tokenizer.encode(user_prefix + user_text + assistant_prefix, add_special_tokens=False).ids
    assistant_ids = tokenizer.encode(assistant_text, add_special_tokens=False).ids + [int(eos)]
    max_total = context_length + 1
    if len(assistant_ids) + 3 > max_total:
        raise ValueError(f"Assistant completion is too long for context length in {record['id']}")
    available_prefix = max_total - len(assistant_ids)
    if len(prefix_ids) > available_prefix:
        # Preserve the user/assistant boundary and all supervised completion tokens.
        tail = prefix_ids[-(available_prefix - 2) :]
        prefix_ids = [int(bos), int(doc), *tail]
    full_ids = [*prefix_ids, *assistant_ids]
    if len(full_ids) < 2:
        raise ValueError(f"Insufficient formatted tokens for {record['id']}")
    inputs = torch.tensor(full_ids[:-1], dtype=torch.long)
    targets = torch.tensor(full_ids[1:], dtype=torch.long)
    first_supervised_target = len(prefix_ids) - 1
    targets[:first_supervised_target] = -100
    if torch.all(targets == -100):
        raise ValueError(f"No assistant-completion targets after formatting {record['id']}")
    return inputs, targets
