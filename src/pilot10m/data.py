"""BPE corpus loading for Aletheia Pilot 10M; evaluation files are never read here."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import torch
from tokenizers import Tokenizer


@dataclass(frozen=True)
class SplitMetadata:
    path: str
    sha256: str
    document_count: int
    token_count: int

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_tokenizer(tokenizer_dir: Path) -> Tokenizer:
    manifest_path = tokenizer_dir / "tokenizer_manifest.json"
    tokenizer_path = tokenizer_dir / "tokenizer.json"
    if not manifest_path.is_file() or not tokenizer_path.is_file():
        raise FileNotFoundError("Expected tokenizer.json and tokenizer_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest.get("corpus_validation_passed"):
        raise ValueError("Refusing tokenizer lineage built from an unvalidated corpus")
    if manifest.get("trained_on_split") != "train":
        raise ValueError("Tokenizer was not trained exclusively on the train split")
    return Tokenizer.from_file(str(tokenizer_path))


def load_split_tokens(
    split_path: Path,
    tokenizer: Tokenizer,
) -> tuple[torch.Tensor, SplitMetadata]:
    if split_path.name not in {"train.jsonl", "validation.jsonl"}:
        raise ValueError("Pilot training loader accepts only train.jsonl or validation.jsonl")
    bos = tokenizer.token_to_id("<bos>")
    eos = tokenizer.token_to_id("<eos>")
    doc = tokenizer.token_to_id("<doc>")
    if None in {bos, eos, doc}:
        raise ValueError("Tokenizer is missing required special tokens")
    all_ids: list[int] = []
    document_count = 0
    with split_path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            record = json.loads(raw_line)
            if not record.get("text"):
                continue
            encoded = tokenizer.encode(record["text"], add_special_tokens=False).ids
            all_ids.extend([int(bos), int(doc), *encoded, int(eos)])
            document_count += 1
    if len(all_ids) < 2:
        raise ValueError(f"Insufficient tokens in {split_path}")
    tokens = torch.tensor(all_ids, dtype=torch.long)
    return tokens, SplitMetadata(
        path=str(split_path.resolve()),
        sha256=sha256_file(split_path),
        document_count=document_count,
        token_count=len(all_ids),
    )


def sample_batch(
    tokens: torch.Tensor,
    batch_size: int,
    context_length: int,
    device: torch.device,
    generator: torch.Generator,
) -> tuple[torch.Tensor, torch.Tensor]:
    available_starts = len(tokens) - context_length - 1
    if available_starts <= 0:
        raise ValueError("Split is shorter than the requested causal context")
    starts = torch.randint(0, available_starts, (batch_size,), generator=generator)
    positions = starts.unsqueeze(1) + torch.arange(context_length).unsqueeze(0)
    x = tokens[positions]
    y = tokens[positions + 1]
    return x.to(device), y.to(device)
