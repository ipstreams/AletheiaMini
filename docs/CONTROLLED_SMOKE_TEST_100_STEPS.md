# Aletheia Tiny: Controlled 100-Step CPU Smoke Test

**Run name:** `smoke`  
**Execution environment:** CPU  
**Seed:** 42  
**Model:** 837,888-parameter byte-level causal Transformer  
**Seed corpus:** Aletheia Seed Corpus v0.1, 8,652 bytes  
**Corpus SHA-256:** `8266252d6eaa298081ce8988b55add8c641bc9e74d0606b310f99adf0c68c9f7`

## Command executed

```bash
python3 src/train.py \
  --run-name smoke \
  --steps 100 \
  --batch-size 8 \
  --eval-interval 20 \
  --eval-batches 4 \
  --checkpoint-interval 50 \
  --device cpu
```

## Result

The controlled smoke test completed successfully. It recorded metrics at the requested twenty-step intervals and wrote both scheduled checkpoints. The loss trend is consistent with the training loop learning local next-byte patterns from the small supplied corpus.

| Step | Batch loss | Mean sampled train loss | Mean sampled validation loss | Gradient norm | Elapsed seconds |
|---:|---:|---:|---:|---:|---:|
| 1 | 5.5609 | 5.2078 | 5.2058 | 4.437 | 0.19 |
| 20 | 4.1191 | 4.0660 | 4.0558 | 2.230 | 1.19 |
| 40 | 3.3446 | 3.2986 | 3.3147 | 1.684 | 2.22 |
| 60 | 2.9357 | 2.9491 | 2.9373 | 1.184 | 3.32 |
| 80 | 2.7559 | 2.7569 | 2.7634 | 0.824 | 4.25 |
| 100 | 2.6417 | 2.6378 | 2.6500 | 1.238 | 5.18 |

The mean sampled training loss decreased by **2.5700** points, from 5.2078 at step 1 to 2.6378 at step 100. The mean sampled validation loss decreased by **2.5558** points, from 5.2058 to 2.6500. The close final train and validation figures are expected for a homogeneous byte-level corpus and short controlled test; they are not evidence of general language competence.

## Verified artifacts

| Artifact | Verification |
|---|---|
| `outputs/smoke/metrics.jsonl` | Contains six recorded metric entries at steps 1, 20, 40, 60, 80, and 100. |
| `outputs/smoke/run_config.json` | Records the exact model, optimizer, corpus, and run settings. |
| `checkpoints/smoke_step_50.pt` | Created successfully; approximately 9.8 MB. |
| `checkpoints/smoke_step_100.pt` | Created successfully; approximately 9.8 MB. |

## Interpretation and next step

The test passes the purpose of a controlled smoke run: it confirms that Aletheia Tiny can train stably from random initialization, log controlled metrics, and checkpoint at the requested intervals. It does not make Aletheia Tiny useful as a broad conversational model, because the approved corpus is deliberately very small and narrow.

The next technically meaningful action is to test generation and checkpoint restoration from `smoke_step_100.pt`, then define an approved larger corpus before beginning the 125M-parameter pilot.
