"""Train Aletheia Tiny from random initialization on an approved byte-level corpus."""

from __future__ import annotations

import argparse
import json
import random
import time
from dataclasses import asdict
from pathlib import Path

import torch

from config import (
    DEFAULT_CHECKPOINT_DIR,
    DEFAULT_DATA_PATH,
    DEFAULT_OUTPUT_DIR,
    ModelConfig,
    TrainConfig,
)
from data import CorpusMetadata, load_byte_corpus, sample_batch
from model import AletheiaTiny


def parse_args() -> argparse.Namespace:
    defaults = TrainConfig()
    parser = argparse.ArgumentParser(description="Train the Aletheia Tiny causal language model.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--steps", type=int, default=defaults.steps)
    parser.add_argument("--batch-size", type=int, default=defaults.batch_size)
    parser.add_argument("--learning-rate", type=float, default=defaults.learning_rate)
    parser.add_argument("--eval-interval", type=int, default=defaults.eval_interval)
    parser.add_argument("--eval-batches", type=int, default=defaults.eval_batches)
    parser.add_argument("--checkpoint-interval", type=int, default=defaults.checkpoint_interval)
    parser.add_argument("--context-length", type=int, default=ModelConfig().context_length)
    parser.add_argument("--seed", type=int, default=defaults.seed)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--run-name", default="aletheia_tiny")
    parser.add_argument("--resume", type=Path, default=None)
    return parser.parse_args()


def select_device(requested: str) -> torch.device:
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is not available")
        return torch.device("cuda")
    if requested == "auto" and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


@torch.no_grad()
def estimate_loss(
    model: AletheiaTiny,
    train_tokens: torch.Tensor,
    validation_tokens: torch.Tensor,
    batch_size: int,
    context_length: int,
    device: torch.device,
    eval_batches: int,
    generator: torch.Generator,
) -> dict[str, float]:
    was_training = model.training
    model.eval()
    losses: dict[str, float] = {}
    for split_name, split_tokens in (("train", train_tokens), ("validation", validation_tokens)):
        values = []
        for _ in range(eval_batches):
            x, y = sample_batch(split_tokens, batch_size, context_length, device, generator)
            _, loss = model(x, y)
            assert loss is not None
            values.append(loss.item())
        losses[f"{split_name}_loss"] = sum(values) / len(values)
    model.train(was_training)
    return losses


def checkpoint_payload(
    model: AletheiaTiny,
    optimizer: torch.optim.Optimizer,
    model_config: ModelConfig,
    train_settings: dict[str, int | float],
    corpus_metadata: CorpusMetadata,
    step: int,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "project": "Aletheia Tiny",
        "model_config": model_config.to_dict(),
        "train_settings": train_settings,
        "corpus_metadata": asdict(corpus_metadata),
        "step": step,
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
        "torch_rng_state": torch.get_rng_state(),
    }
    if torch.cuda.is_available():
        payload["cuda_rng_state_all"] = torch.cuda.get_rng_state_all()
    return payload


def save_checkpoint(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".tmp")
    torch.save(payload, temporary_path)
    temporary_path.replace(path)


def main() -> None:
    args = parse_args()
    if args.steps <= 0 or args.batch_size <= 0:
        raise ValueError("steps and batch-size must be positive")
    if args.eval_interval <= 0 or args.checkpoint_interval <= 0:
        raise ValueError("evaluation and checkpoint intervals must be positive")

    set_seed(args.seed)
    device = select_device(args.device)
    train_defaults = TrainConfig()
    model_config = ModelConfig(context_length=args.context_length)
    train_tokens, validation_tokens, corpus_metadata = load_byte_corpus(
        args.data, train_defaults.validation_fraction
    )
    if len(validation_tokens) <= model_config.context_length + 1:
        raise ValueError("Validation split is too small for the configured context length")

    model = AletheiaTiny(model_config).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        betas=(0.9, 0.95),
        weight_decay=train_defaults.weight_decay,
    )
    start_step = 0

    if args.resume is not None:
        checkpoint = torch.load(args.resume, map_location=device, weights_only=False)
        saved_config = ModelConfig(**checkpoint["model_config"])
        if saved_config != model_config:
            raise ValueError("Checkpoint model configuration does not match requested configuration")
        model.load_state_dict(checkpoint["model_state"])
        optimizer.load_state_dict(checkpoint["optimizer_state"])
        torch.set_rng_state(checkpoint["torch_rng_state"])
        if device.type == "cuda" and "cuda_rng_state_all" in checkpoint:
            torch.cuda.set_rng_state_all(checkpoint["cuda_rng_state_all"])
        start_step = int(checkpoint["step"])

    output_dir = DEFAULT_OUTPUT_DIR / args.run_name
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "metrics.jsonl"
    config_path = output_dir / "run_config.json"
    train_settings = {
        "seed": args.seed,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "weight_decay": train_defaults.weight_decay,
        "max_grad_norm": train_defaults.max_grad_norm,
        "steps": args.steps,
        "eval_interval": args.eval_interval,
        "eval_batches": args.eval_batches,
        "checkpoint_interval": args.checkpoint_interval,
        "validation_fraction": train_defaults.validation_fraction,
    }
    config_path.write_text(
        json.dumps(
            {
                "project": "Aletheia Tiny",
                "device": str(device),
                "model_config": model_config.to_dict(),
                "train_settings": train_settings,
                "corpus_metadata": asdict(corpus_metadata),
                "parameter_count": model.parameter_count,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    train_generator = torch.Generator(device="cpu").manual_seed(args.seed)
    evaluation_generator = torch.Generator(device="cpu").manual_seed(args.seed + 1)
    started_at = time.perf_counter()
    print(f"Aletheia Tiny: {model.parameter_count:,} parameters on {device}")
    print(f"Corpus: {corpus_metadata.total_bytes:,} bytes, SHA-256 {corpus_metadata.sha256}")

    with metrics_path.open("a", encoding="utf-8") as metrics_file:
        for step in range(start_step, args.steps):
            model.train()
            x, y = sample_batch(
                train_tokens,
                args.batch_size,
                model_config.context_length,
                device,
                train_generator,
            )
            _, loss = model(x, y)
            assert loss is not None
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            gradient_norm = torch.nn.utils.clip_grad_norm_(
                model.parameters(), train_defaults.max_grad_norm
            )
            optimizer.step()

            completed_step = step + 1
            if completed_step == 1 or completed_step % args.eval_interval == 0 or completed_step == args.steps:
                losses = estimate_loss(
                    model,
                    train_tokens,
                    validation_tokens,
                    args.batch_size,
                    model_config.context_length,
                    device,
                    args.eval_batches,
                    evaluation_generator,
                )
                elapsed_seconds = time.perf_counter() - started_at
                record = {
                    "step": completed_step,
                    "batch_loss": loss.item(),
                    "gradient_norm": float(gradient_norm),
                    "elapsed_seconds": elapsed_seconds,
                    **losses,
                }
                metrics_file.write(json.dumps(record) + "\n")
                metrics_file.flush()
                print(
                    f"step={completed_step:>5} batch={record['batch_loss']:.4f} "
                    f"train={record['train_loss']:.4f} valid={record['validation_loss']:.4f} "
                    f"grad={record['gradient_norm']:.3f}"
                )

            if completed_step % args.checkpoint_interval == 0 or completed_step == args.steps:
                checkpoint_path = DEFAULT_CHECKPOINT_DIR / f"{args.run_name}_step_{completed_step}.pt"
                payload = checkpoint_payload(
                    model,
                    optimizer,
                    model_config,
                    train_settings,
                    corpus_metadata,
                    completed_step,
                )
                save_checkpoint(checkpoint_path, payload)
                print(f"checkpoint={checkpoint_path}")


if __name__ == "__main__":
    main()
