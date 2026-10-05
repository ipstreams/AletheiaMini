"""Exit successfully only when PyTorch has a usable CUDA device."""
from __future__ import annotations

import sys

import torch


def main() -> None:
    if not torch.cuda.is_available():
        print("CUDA is unavailable to PyTorch", file=sys.stderr)
        raise SystemExit(1)
    index = torch.cuda.current_device()
    properties = torch.cuda.get_device_properties(index)
    print(f"CUDA device {index}: {properties.name}; memory={properties.total_memory // (1024 * 1024)} MiB")


if __name__ == "__main__":
    main()
