"""Assistant-completion supervised fine tuning for Aletheia Pilot 10M."""
from __future__ import annotations

import argparse
import json
import random
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

from pilot10m.config import PILOT_MODEL_ID, TOKENIZER_DIR, PilotModelConfig
from pilot10m.data import load_tokenizer, sha256_file
from pilot10m.instruction_data import format_supervised_example, load_instruction_dataset
from pilot10m.model import AletheiaPilotLM


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validation_loss(
    model: AletheiaPilotLM,
    records: list[dict],
    tokenizer,
    device: torch.device,
) -> float:
    model.eval()
    losses: list[float] = []
    with torch.no_grad():
        for record in records:
            x, y = format_supervised_example(record, tokenizer, model.config.context_length)
            _, loss = model(x.unsqueeze(0).to(device), y.unsqueeze(0).to(device))
            assert loss is not None
            losses.append(float(loss.item()))
    model.train()
    return sum(losses) / len(losses)


def save_checkpoint(
    path: Path,
    model: AletheiaPilotLM,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    step: int,
    fine_tuning_config: dict,
    lineage: dict,
    validation_loss_value: float,
) -> None:
    torch.save(
        {
            "checkpoint_format": "aletheia-pilot10m-instruction-v1",
            "model_id": f"{PILOT_MODEL_ID}-instruction-v1",
            "base_model_id": PILOT_MODEL_ID,
            "base_checkpoint_sha256": lineage["base_checkpoint_sha256"],
            "fresh_base_checkpoint": True,
            "instruction_tuning": True,
            "epoch": epoch,
            "step": step,
            "validation_loss": validation_loss_value,
            "model_config": model.config.to_dict(),
            "fine_tuning_config": fine_tuning_config,
            "lineage": lineage,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "torch_rng_state": torch.get_rng_state(),
        },
        path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-checkpoint", type=Path, required=True)
    parser.add_argument("--run-id", default="aletheia-pilot-10m-instruction-v1-cpu")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--max-grad-norm", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=20260827)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--cpu-threads", type=int, default=3)
    args = parser.parse_args()
    if args.epochs < 1:
        raise ValueError("epochs must be positive")
    if not args.base_checkpoint.is_file():
        raise FileNotFoundError(args.base_checkpoint)
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    if args.device == "cpu":
        torch.set_num_threads(args.cpu_threads)

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device(args.device)
    run_dir = Path(__file__).resolve().parents[2] / "runs" / "pilot10m" / args.run_id
    if run_dir.exists():
        raise FileExistsError(f"Run directory already exists: {run_dir}")
    checkpoint_dir = run_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True)

    base = torch.load(args.base_checkpoint, map_location=device, weights_only=False)
    if base.get("checkpoint_format") != "aletheia-pilot10m-v1" or base.get("model_id") != PILOT_MODEL_ID:
        raise ValueError("Base checkpoint is not the required fresh Aletheia Pilot 10M format")
    if not base.get("fresh_random_initialization"):
        raise ValueError("Base checkpoint is not documented as fresh random initialization")
    model_config = PilotModelConfig(**base["model_config"])
    model = AletheiaPilotLM(model_config).to(device)
    model.load_state_dict(base["model_state"])
    tokenizer = load_tokenizer(TOKENIZER_DIR)
    train_records, validation_records, data_metadata = load_instruction_dataset()

    config = {
        "epochs": args.epochs,
        "learning_rate": args.learning_rate,
        "weight_decay": args.weight_decay,
        "max_grad_norm": args.max_grad_norm,
        "seed": args.seed,
        "device": args.device,
        "loss_scope": "assistant_completion_only",
        "message_format": "User:\\n{user}\\nAssistant:\\n{assistant}",
        "system_prompt_injected": False,
        "tool_context": "none",
    }
    lineage = {
        "base_checkpoint_path": str(args.base_checkpoint.resolve()),
        "base_checkpoint_sha256": sha256_file(args.base_checkpoint),
        "base_training_lineage": base["lineage"],
        "instruction_data": data_metadata.to_dict(),
        "tokenizer_id": "pilot-v0.2-bpe-2000",
        "tokenizer_manifest_sha256": sha256_file(TOKENIZER_DIR / "tokenizer_manifest.json"),
        "locked_evaluation_suite": "aletheia-epistemic-eval-v1",
        "locked_evaluation_excluded_from_training": True,
    }
    run_record = {
        "run_id": args.run_id,
        "started_utc": utc_now(),
        "model_id": f"{PILOT_MODEL_ID}-instruction-v1",
        "base_model_id": PILOT_MODEL_ID,
        "fine_tuning_config": config,
        "lineage": lineage,
    }
    run_dir.mkdir(exist_ok=True)
    (run_dir / "run_record.json").write_text(json.dumps(run_record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)
    metrics_path = run_dir / "metrics.jsonl"
    best_validation = float("inf")
    best_epoch = 0
    step = 0
    started = time.perf_counter()
    model.train()
    for epoch in range(1, args.epochs + 1):
        order = list(range(len(train_records)))
        random.Random(args.seed + epoch).shuffle(order)
        train_losses: list[float] = []
        for index in order:
            record = train_records[index]
            x, y = format_supervised_example(record, tokenizer, model_config.context_length)
            optimizer.zero_grad(set_to_none=True)
            _, loss = model(x.unsqueeze(0).to(device), y.unsqueeze(0).to(device))
            assert loss is not None
            loss.backward()
            gradient_norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), args.max_grad_norm).item())
            optimizer.step()
            train_losses.append(float(loss.item()))
            step += 1
        current_validation = validation_loss(model, validation_records, tokenizer, device)
        event = {
            "epoch": epoch,
            "step": step,
            "mean_train_loss": sum(train_losses) / len(train_losses),
            "validation_loss": current_validation,
            "last_gradient_norm": gradient_norm,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "utc": utc_now(),
        }
        with metrics_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
        print(json.dumps(event, sort_keys=True), flush=True)
        save_checkpoint(checkpoint_dir / "last.pt", model, optimizer, epoch, step, config, lineage, current_validation)
        if current_validation < best_validation:
            best_validation = current_validation
            best_epoch = epoch
            save_checkpoint(checkpoint_dir / "best_validation.pt", model, optimizer, epoch, step, config, lineage, current_validation)

    selection = {
        "selection_metric": "mean assistant-completion cross-entropy on instruction validation.jsonl",
        "selected_checkpoint": "checkpoints/best_validation.pt",
        "selected_epoch": best_epoch,
        "selected_validation_loss": best_validation,
        "final_epoch": args.epochs,
        "final_step": step,
        "completed_utc": utc_now(),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    (run_dir / "checkpoint_selection.json").write_text(json.dumps(selection, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shutil.copy2(checkpoint_dir / "best_validation.pt", run_dir / "frozen_selected_checkpoint.pt")
    print(json.dumps(selection, sort_keys=True))


if __name__ == "__main__":
    main()
