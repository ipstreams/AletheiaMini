"""Configuration and immutable lineage constants for Aletheia Pilot 10M."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORPUS_BUILD_DIR = PROJECT_ROOT / "data" / "corpus_builds" / "pilot-v0.2"
TOKENIZER_DIR = PROJECT_ROOT / "data" / "tokenizers" / "pilot-v0.2-bpe-2000"
EVALUATION_SUITE = PROJECT_ROOT / "evaluations" / "suites" / "aletheia-epistemic-eval-v1" / "suite.jsonl"


@dataclass(frozen=True)
class PilotModelConfig:
    """A 10.656M-parameter decoder-only Transformer for v0.2 BPE data."""

    vocab_size: int = 2000
    context_length: int = 128
    n_layers: int = 5
    n_heads: int = 6
    d_model: int = 384
    d_ff: int = 1792
    dropout: float = 0.0

    def __post_init__(self) -> None:
        if self.d_model % self.n_heads:
            raise ValueError("d_model must be divisible by n_heads")
        if self.context_length < 2:
            raise ValueError("context_length must be at least 2")

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


@dataclass(frozen=True)
class PilotTrainConfig:
    """Controlled default training parameters for the CPU pilot baseline."""

    seed: int = 20260826
    steps: int = 300
    batch_size: int = 4
    learning_rate: float = 3e-4
    weight_decay: float = 0.1
    max_grad_norm: float = 1.0
    eval_interval: int = 50
    eval_batches: int = 8
    checkpoint_interval: int = 100
    device: str = "cpu"
    cpu_threads: int = 3

    def to_dict(self) -> dict[str, int | float | str]:
        return asdict(self)


PILOT_MODEL_ID = "aletheia-pilot-10m-v0.1"
PILOT_RUN_ID = "aletheia-pilot-10m-v0.1-cpu-300step"
SYSTEM_PROMPT_ID = "base-preinstruction-none"
TOOL_CONTEXT = "none"
