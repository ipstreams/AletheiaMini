"""Evaluate a saved Aletheia Tiny checkpoint on the fixed held-out split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from config import DEFAULT_DATA_PATH, ModelConfig
from data import load_byte_corpus, sample_batch
from model import AletheiaTiny


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate an Aletheia Tiny checkpoint.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--batches", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=43)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    return parser.parse_args()


def select_device(requested: str) -> torch.device:
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is not available")
        return torch.device("cuda")
    if requested == "auto" and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


@torch.no_grad()
def mean_loss(
    model: AletheiaTiny,
    tokens: torch.Tensor,
    batch_size: int,
    batches: int,
    device: torch.device,
    generator: torch.Generator,
) -> float:
    model.eval()
    losses: list[float] = []
    for _ in range(batches):
        x, y = sample_batch(tokens, batch_size, model.config.context_length, device, generator)
        _, loss = model(x, y)
        assert loss is not None
        losses.append(loss.item())
    return sum(losses) / len(losses)


def main() -> None:
    args = parse_args()
    if args.batches <= 0 or args.batch_size <= 0:
        raise ValueError("batches and batch-size must be positive")
    device = select_device(args.device)
    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
    model = AletheiaTiny(ModelConfig(**checkpoint["model_config"])).to(device)
    model.load_state_dict(checkpoint["model_state"])
    train_tokens, validation_tokens, metadata = load_byte_corpus(
        args.data, float(checkpoint["train_settings"]["validation_fraction"])
    )
    generator = torch.Generator(device="cpu").manual_seed(args.seed)
    results = {
        "project": "Aletheia Tiny",
        "checkpoint": str(args.checkpoint.resolve()),
        "checkpoint_step": int(checkpoint["step"]),
        "corpus_sha256": metadata.sha256,
        "train_loss": mean_loss(model, train_tokens, args.batch_size, args.batches, device, generator),
        "validation_loss": mean_loss(
            model, validation_tokens, args.batch_size, args.batches, device, generator
        ),
        "evaluation_batches": args.batches,
        "device": str(device),
    }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
