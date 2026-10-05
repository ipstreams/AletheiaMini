"""Generate unedited held-out responses from a fresh Aletheia Pilot 10M checkpoint."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import torch

from pilot10m.config import EVALUATION_SUITE, PILOT_MODEL_ID, SYSTEM_PROMPT_ID, TOKENIZER_DIR, TOOL_CONTEXT, PilotModelConfig
from pilot10m.data import load_tokenizer, sha256_file
from pilot10m.model import AletheiaPilotLM


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=48)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260826)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--cpu-threads", type=int, default=3)
    args = parser.parse_args()
    if not args.checkpoint.is_file():
        raise FileNotFoundError(args.checkpoint)
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    if args.device == "cpu":
        torch.set_num_threads(args.cpu_threads)

    output_dir = Path(__file__).resolve().parents[2] / "evaluations" / "runs" / "pilot10m" / args.run_id
    if output_dir.exists():
        raise FileExistsError(f"Evaluation output already exists: {output_dir}")
    output_dir.mkdir(parents=True)
    device = torch.device(args.device)
    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
    checkpoint_format = checkpoint.get("checkpoint_format")
    supported_formats = {"aletheia-pilot10m-v1", "aletheia-pilot10m-instruction-v1"}
    if checkpoint_format not in supported_formats:
        raise ValueError("Checkpoint does not belong to a supported isolated Pilot 10M lineage")
    if checkpoint_format == "aletheia-pilot10m-v1" and not checkpoint.get("fresh_random_initialization"):
        raise ValueError("Refusing a base checkpoint not documented as fresh random initialization")
    if checkpoint_format == "aletheia-pilot10m-instruction-v1" and not checkpoint.get("fresh_base_checkpoint"):
        raise ValueError("Refusing an instruction checkpoint without a fresh Pilot 10M base lineage")
    model_config = PilotModelConfig(**checkpoint["model_config"])
    model = AletheiaPilotLM(model_config).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    tokenizer = load_tokenizer(TOKENIZER_DIR)
    bos = tokenizer.token_to_id("<bos>")
    if bos is None:
        raise ValueError("Tokenizer is missing <bos>")
    suite_manifest = EVALUATION_SUITE.with_name("suite_manifest.json")
    suite_sha256 = sha256_file(EVALUATION_SUITE)
    training_lineage = checkpoint["lineage"].get("base_training_lineage", checkpoint["lineage"])
    record = {
        "run_id": args.run_id,
        "suite_id": "aletheia-epistemic-eval-v1",
        "suite_sha256": suite_sha256,
        "model_id": checkpoint["model_id"],
        "checkpoint_format": checkpoint_format,
        "checkpoint_path": str(args.checkpoint.resolve()),
        "checkpoint_sha256": sha256_file(args.checkpoint),
        "checkpoint_step": checkpoint["step"],
        "fresh_random_initialization": bool(checkpoint.get("fresh_random_initialization") or checkpoint.get("fresh_base_checkpoint")),
        "instruction_tuning": bool(checkpoint.get("instruction_tuning", False)),
        "system_prompt_id": SYSTEM_PROMPT_ID,
        "tool_context": TOOL_CONTEXT,
        "supplied_evidence": [],
        "session_mode": "clean_negative_control",
        "decoding": {
            "max_new_tokens": args.max_new_tokens,
            "temperature": args.temperature,
            "top_k": args.top_k,
            "seed": args.seed,
            "device": args.device,
        },
        "tokenizer_id": "pilot-v0.2-bpe-2000",
        "tokenizer_manifest_sha256": sha256_file(TOKENIZER_DIR / "tokenizer_manifest.json"),
        "corpus_build_id": training_lineage["corpus_build_id"],
        "corpus_build_manifest_sha256": training_lineage["corpus_build_manifest_sha256"],
        "evaluation_suite_manifest_sha256": sha256_file(suite_manifest),
        "evaluation_suite_excluded_from_training": True,
        "started_utc": utc_now(),
    }
    (output_dir / "run_record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    response_path = output_dir / "responses_unscored.jsonl"
    with EVALUATION_SUITE.open(encoding="utf-8") as suite, response_path.open("w", encoding="utf-8") as output:
        for index, raw_line in enumerate(suite):
            item = json.loads(raw_line)
            if not item.get("evaluation_only") or not item.get("exclude_from_training"):
                raise ValueError(f"Suite item is not correctly marked held out: {item['item_id']}")
            prompt_ids = tokenizer.encode(item["prompt"], add_special_tokens=False).ids
            prompt_ids = [int(bos), *prompt_ids]
            if len(prompt_ids) >= model_config.context_length:
                prompt_ids = prompt_ids[-(model_config.context_length - 1) :]
                prompt_ids.insert(0, int(bos))
            prompt = torch.tensor([prompt_ids], dtype=torch.long, device=device)
            torch.manual_seed(args.seed + index)
            generated = model.generate(
                prompt,
                max_new_tokens=args.max_new_tokens,
                temperature=args.temperature,
                top_k=args.top_k,
            )
            completion_ids = generated[0, len(prompt_ids) :].tolist()
            response = tokenizer.decode(completion_ids, skip_special_tokens=True)
            result = {
                "run_id": args.run_id,
                "suite_id": "aletheia-epistemic-eval-v1",
                "suite_item_id": item["item_id"],
                "question_id": item["question_id"],
                "domain": item["domain"],
                "domain_title": item["domain_title"],
                "model_id": checkpoint["model_id"],
                "system_prompt_id": SYSTEM_PROMPT_ID,
                "tool_context": TOOL_CONTEXT,
                "supplied_evidence": [],
                "prompt": item["prompt"],
                "response": response,
                "evaluation_only": True,
                "exclude_from_training": True,
                "generated_utc": utc_now(),
            }
            output.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
            print(json.dumps({"item_id": item["item_id"], "response_characters": len(response)}), flush=True)
    record["completed_utc"] = utc_now()
    record["response_file"] = str(response_path.resolve())
    record["response_file_sha256"] = sha256_file(response_path)
    (output_dir / "run_summary.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
