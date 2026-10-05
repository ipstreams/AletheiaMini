"""Tests for byte-level data loading and causal batch creation."""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from data import load_byte_corpus, sample_batch  # noqa: E402


class DataTests(unittest.TestCase):
    def test_load_byte_corpus_preserves_bytes_and_records_hash(self) -> None:
        content = bytes(range(256)) * 3
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.bin"
            path.write_bytes(content)
            train, validation, metadata = load_byte_corpus(path, validation_fraction=0.2)

        self.assertEqual(len(train), int(len(content) * 0.8))
        self.assertEqual(len(validation), len(content) - len(train))
        self.assertEqual(metadata.sha256, hashlib.sha256(content).hexdigest())
        self.assertEqual(metadata.total_bytes, len(content))
        self.assertEqual(train.dtype, torch.long)

    def test_sample_batch_is_shifted_by_one_token(self) -> None:
        tokens = torch.arange(300, dtype=torch.long) % 256
        generator = torch.Generator().manual_seed(7)
        x, y = sample_batch(
            tokens=tokens,
            batch_size=5,
            context_length=16,
            device=torch.device("cpu"),
            generator=generator,
        )
        self.assertEqual(tuple(x.shape), (5, 16))
        self.assertEqual(tuple(y.shape), (5, 16))
        self.assertTrue(torch.equal(y[:, :-1], x[:, 1:]))


if __name__ == "__main__":
    unittest.main()
