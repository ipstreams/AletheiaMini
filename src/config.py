"""Versioned configuration objects for the Aletheia Tiny training demonstration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ModelConfig:
    """Decoder-only transformer settings for a small from-scratch model."""

    vocab_size: int = 256
    context_length: int = 128
    n_layers: int = 4
    n_heads: int = 4
    d_model: int = 128
    d_ff: int = 512
    dropout: float = 0.0

    def __post_init__(self) -> None:
        if self.d_model % self.n_heads != 0:
            raise ValueError("d_model must be divisible by n_heads")
        if self.context_length < 2:
            raise ValueError("context_length must be at least 2")

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


@dataclass(frozen=True)
class TrainConfig:
    """Reproducible default values for a compact smoke-training run."""

    seed: int = 42
    batch_size: int = 16
    learning_rate: float = 3e-4
    weight_decay: float = 0.1
    max_grad_norm: float = 1.0
    steps: int = 400
    eval_interval: int = 50
    eval_batches: int = 20
    checkpoint_interval: int = 100
    validation_fraction: float = 0.10

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "aletheia_seed.txt"
DEFAULT_CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"
