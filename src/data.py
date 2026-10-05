"""Byte-level data loading and deterministic causal-language-model batches."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import torch


@dataclass(frozen=True)
class CorpusMetadata:
    """Traceable properties of the corpus used for a training run."""

    source_path: str
    sha256: str
    total_bytes: int
    train_bytes: int
    validation_bytes: int
    validation_fraction: float


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_byte_corpus(
    path: str | Path,
    validation_fraction: float = 0.10,
) -> tuple[torch.Tensor, torch.Tensor, CorpusMetadata]:
    """Load a user-approved file as byte tokens and make a fixed train/validation split."""

    corpus_path = Path(path).expanduser().resolve()
    if not corpus_path.is_file():
        raise FileNotFoundError(f"Corpus does not exist: {corpus_path}")
    if not 0.0 < validation_fraction < 0.5:
        raise ValueError("validation_fraction must be between 0 and 0.5")

    raw = corpus_path.read_bytes()
    if len(raw) < 512:
        raise ValueError("Corpus must contain at least 512 bytes for this demonstration")

    split_index = int(len(raw) * (1.0 - validation_fraction))
    train = torch.tensor(list(raw[:split_index]), dtype=torch.long)
    validation = torch.tensor(list(raw[split_index:]), dtype=torch.long)
    metadata = CorpusMetadata(
        source_path=str(corpus_path),
        sha256=_sha256(corpus_path),
        total_bytes=len(raw),
        train_bytes=len(train),
        validation_bytes=len(validation),
        validation_fraction=validation_fraction,
    )
    return train, validation, metadata


def sample_batch(
    tokens: torch.Tensor,
    batch_size: int,
    context_length: int,
    device: torch.device,
    generator: torch.Generator | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Sample independent causal-language-model input and target windows."""

    if tokens.ndim != 1:
        raise ValueError("tokens must be a one-dimensional tensor")
    available_starts = len(tokens) - context_length - 1
    if available_starts <= 0:
        raise ValueError(
            f"Need more than {context_length + 1} tokens; received {len(tokens)}"
        )

    starts = torch.randint(
        low=0,
        high=available_starts,
        size=(batch_size,),
        generator=generator,
    )
    positions = starts.unsqueeze(1) + torch.arange(context_length).unsqueeze(0)
    x = tokens[positions]
    y = tokens[positions + 1]
    return x.to(device, non_blocking=True), y.to(device, non_blocking=True)
