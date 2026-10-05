"""Generate byte-level text from a trained Aletheia Tiny checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch.nn import functional as F

from config import DEFAULT_CHECKPOINT_DIR, ModelConfig
from model import AletheiaTiny


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate text with an Aletheia Tiny checkpoint.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--tokens", type=int, default=160)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42)
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


def load_model(path: Path, device: torch.device) -> AletheiaTiny:
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    model = AletheiaTiny(ModelConfig(**checkpoint["model_config"])).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    return model


@torch.no_grad()
def generate(
    model: AletheiaTiny,
    prompt: str,
    tokens_to_generate: int,
    temperature: float,
    top_k: int,
    generator: torch.Generator,
) -> str:
    if not prompt:
        raise ValueError("prompt cannot be empty")
    if tokens_to_generate < 0:
        raise ValueError("tokens must be non-negative")
    if temperature <= 0:
        raise ValueError("temperature must be positive")

    device = next(model.parameters()).device
    encoded = list(prompt.encode("utf-8", errors="replace"))
    token_ids = torch.tensor([encoded], dtype=torch.long, device=device)
    for _ in range(tokens_to_generate):
        context = token_ids[:, -model.config.context_length :]
        logits, _ = model(context)
        logits = logits[:, -1, :] / temperature
        if top_k > 0:
            k = min(top_k, logits.size(-1))
            threshold = torch.topk(logits, k).values[:, [-1]]
            logits = logits.masked_fill(logits < threshold, float("-inf"))
        probabilities = F.softmax(logits, dim=-1)
        next_token = torch.multinomial(probabilities, num_samples=1, generator=generator)
        token_ids = torch.cat((token_ids, next_token), dim=1)
    return bytes(token_ids[0].tolist()).decode("utf-8", errors="replace")


def main() -> None:
    args = parse_args()
    device = select_device(args.device)
    model = load_model(args.checkpoint, device)
    generator = torch.Generator(device=device).manual_seed(args.seed)
    text = generate(
        model=model,
        prompt=args.prompt,
        tokens_to_generate=args.tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        generator=generator,
    )
    print(text)


if __name__ == "__main__":
    main()
