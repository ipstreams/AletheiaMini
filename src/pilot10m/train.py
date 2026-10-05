"""Controlled fresh-from-random training for Aletheia Pilot 10M."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

from pilot10m.config import (
    CORPUS_BUILD_DIR,
    PILOT_MODEL_ID,
    PILOT_RUN_ID,
    TOKENIZER_DIR,
    PilotModelConfig,
    PilotTrainConfig,
)
from pilot10m.data import load_split_tokens, load_tokenizer, sample_batch, sha256_file
from pilot10m.model import AletheiaPilotLM


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_json(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def evaluate_loss(
    model: AletheiaPilotLM,
    tokens: torch.Tensor,
    config: PilotTrainConfig,
    device: torch.device,
    step: int,
) -> float:
    model.eval()
    generator = torch.Generator().manual_seed(config.seed + 100000 + step)
    losses: list[float] = []
    with torch.no_grad():
        for _ in range(config.eval_batches):
            x, y = sample_batch(tokens, config.batch_size, model.config.context_length, device, generator)
            _, loss = model(x, y)
            assert loss is not None
            losses.append(float(loss.item()))
    model.train()
    return sum(losses) / len(losses)


def save_checkpoint(
    path: Path,
    model: AletheiaPilotLM,
    optimizer: torch.optim.Optimizer,
    step: int,
    model_config: PilotModelConfig,
    train_config: PilotTrainConfig,
    lineage: dict[str, object],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "checkpoint_format": "aletheia-pilot10m-v1",
            "model_id": PILOT_MODEL_ID,
            "fresh_random_initialization": True,
            "step": step,
            "model_config": model_config.to_dict(),
            "training_config": train_config.to_dict(),
            "lineage": lineage,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "torch_rng_state": torch.get_rng_state(),
        },
        path,
    )


def main() -> None:
    defaults = PilotTrainConfig()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=PILOT_RUN_ID)
    parser.add_argument("--steps", type=int, default=defaults.steps)
    parser.add_argument("--batch-size", type=int, default=defaults.batch_size)
    parser.add_argument("--learning-rate", type=float, default=defaults.learning_rate)
    parser.add_argument("--weight-decay", type=float, default=defaults.weight_decay)
    parser.add_argument("--max-grad-norm", type=float, default=defaults.max_grad_norm)
    parser.add_argument("--eval-interval", type=int, default=defaults.eval_interval)
    parser.add_argument("--eval-batches", type=int, default=defaults.eval_batches)
    parser.add_argument("--checkpoint-interval", type=int, default=defaults.checkpoint_interval)
    parser.add_argument("--seed", type=int, default=defaults.seed)
    parser.add_argument("--device", default=defaults.device, choices=("cpu", "cuda"))
    parser.add_argument("--cpu-threads", type=int, default=defaults.cpu_threads)
    args = parser.parse_args()
    if args.steps < 1 or args.batch_size < 1:
        raise ValueError("steps and batch-size must be positive")
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")

    config = PilotTrainConfig(
        seed=args.seed,
        steps=args.steps,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        max_grad_norm=args.max_grad_norm,
        eval_interval=args.eval_interval,
        eval_batches=args.eval_batches,
        checkpoint_interval=args.checkpoint_interval,
        device=args.device,
        cpu_threads=args.cpu_threads,
    )
    model_config = PilotModelConfig()
    if args.device == "cpu":
        torch.set_num_threads(config.cpu_threads)
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    device = torch.device(config.device)

    run_dir = Path(__file__).resolve().parents[2] / "runs" / "pilot10m" / args.run_id
    checkpoints_dir = run_dir / "checkpoints"
    if run_dir.exists():
        raise FileExistsError(f"Run directory already exists: {run_dir}")
    run_dir.mkdir(parents=True)

    validation_report = json.loads((CORPUS_BUILD_DIR / "validation_report.json").read_text(encoding="utf-8"))
    if not validation_report.get("passed"):
        raise ValueError("Refusing to train from a corpus that did not pass normal validation")
    tokenizer = load_tokenizer(TOKENIZER_DIR)
    train_tokens, train_metadata = load_split_tokens(CORPUS_BUILD_DIR / "train.jsonl", tokenizer)
    validation_tokens, validation_metadata = load_split_tokens(CORPUS_BUILD_DIR / "validation.jsonl", tokenizer)
    lineage = {
        "corpus_build_id": "pilot-v0.2",
        "corpus_build_manifest_sha256": sha256_file(CORPUS_BUILD_DIR / "corpus_build_manifest.json"),
        "corpus_validation_report_sha256": sha256_file(CORPUS_BUILD_DIR / "validation_report.json"),
        "tokenizer_id": "pilot-v0.2-bpe-2000",
        "tokenizer_manifest_sha256": sha256_file(TOKENIZER_DIR / "tokenizer_manifest.json"),
        "train_split": train_metadata.to_dict(),
        "validation_split": validation_metadata.to_dict(),
        "evaluation_suite_excluded_from_training": True,
        "evaluation_suite_path_not_read": str(Path(__file__).resolve().parents[2] / "evaluations" / "suites" / "aletheia-epistemic-eval-v1" / "suite.jsonl"),
    }
    model = AletheiaPilotLM(model_config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    training_generator = torch.Generator().manual_seed(config.seed + 1)
    run_record = {
        "run_id": args.run_id,
        "started_utc": utc_now(),
        "model_id": PILOT_MODEL_ID,
        "fresh_random_initialization": True,
        "model_parameter_count": model.parameter_count,
        "model_config": model_config.to_dict(),
        "training_config": config.to_dict(),
        "lineage": lineage,
        "training_config_sha256": sha256_json({"model": model_config.to_dict(), "training": config.to_dict(), "lineage": lineage}),
    }
    (run_dir / "run_record.json").write_text(json.dumps(run_record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    metrics_path = run_dir / "metrics.jsonl"
    started = time.perf_counter()
    model.train()
    for step in range(1, config.steps + 1):
        x, y = sample_batch(train_tokens, config.batch_size, model_config.context_length, device, training_generator)
        optimizer.zero_grad(set_to_none=True)
        _, loss = model(x, y)
        assert loss is not None
        loss.backward()
        grad_norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm).item())
        optimizer.step()
        if step == 1 or step % config.eval_interval == 0 or step == config.steps:
            validation_loss = evaluate_loss(model, validation_tokens, config, device, step)
            event = {
                "step": step,
                "train_loss": float(loss.item()),
                "validation_loss": validation_loss,
                "gradient_norm": grad_norm,
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "utc": utc_now(),
            }
            with metrics_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, sort_keys=True) + "\n")
            print(json.dumps(event, sort_keys=True), flush=True)
        if step % config.checkpoint_interval == 0 or step == config.steps:
            save_checkpoint(checkpoints_dir / f"step_{step:05d}.pt", model, optimizer, step, model_config, config, lineage)

    completed = {
        **run_record,
        "completed_utc": utc_now(),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "final_checkpoint": str((checkpoints_dir / f"step_{config.steps:05d}.pt").resolve()),
    }
    (run_dir / "run_summary.json").write_text(json.dumps(completed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"run_dir": str(run_dir), "parameter_count": model.parameter_count}, sort_keys=True))


if __name__ == "__main__":
    main()
