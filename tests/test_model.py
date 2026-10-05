"""Tests for the Aletheia Tiny causal transformer."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config import ModelConfig  # noqa: E402
from model import AletheiaTiny  # noqa: E402


class ModelTests(unittest.TestCase):
    def setUp(self) -> None:
        torch.manual_seed(11)
        self.config = ModelConfig(
            context_length=16,
            n_layers=2,
            n_heads=4,
            d_model=32,
            d_ff=128,
            dropout=0.0,
        )
        self.model = AletheiaTiny(self.config)

    def test_forward_returns_vocab_logits_and_scalar_loss(self) -> None:
        x = torch.randint(0, 256, (3, 16))
        y = torch.randint(0, 256, (3, 16))
        logits, loss = self.model(x, y)
        self.assertEqual(tuple(logits.shape), (3, 16, 256))
        self.assertIsNotNone(loss)
        assert loss is not None
        self.assertEqual(loss.ndim, 0)
        self.assertTrue(torch.isfinite(loss))

    def test_future_tokens_do_not_change_earlier_logits(self) -> None:
        self.model.eval()
        x = torch.randint(0, 256, (1, 16))
        changed = x.clone()
        changed[:, 10:] = (changed[:, 10:] + 17) % 256
        original_logits, _ = self.model(x)
        changed_logits, _ = self.model(changed)
        self.assertTrue(torch.allclose(original_logits[:, :10], changed_logits[:, :10], atol=1e-6))

    def test_single_optimization_step_updates_parameters(self) -> None:
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-3)
        x = torch.randint(0, 256, (2, 16))
        y = torch.randint(0, 256, (2, 16))
        before = self.model.token_embedding.weight.detach().clone()
        _, loss = self.model(x, y)
        assert loss is not None
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        self.assertFalse(torch.equal(before, self.model.token_embedding.weight.detach()))


if __name__ == "__main__":
    unittest.main()
