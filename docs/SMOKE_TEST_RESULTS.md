# Aletheia Tiny: Local Smoke-Test Results

**Test date:** August 2026  
**Environment:** Local CPU execution  
**Corpus:** Aletheia Seed Corpus v0.1  
**Corpus SHA-256:** `8266252d6eaa298081ce8988b55add8c641bc9e74d0606b310f99adf0c68c9f7`

## Validation summary

The initial implementation was validated as an end-to-end causal language-model pipeline. The unit-test suite passed all five tests, covering byte-corpus loading, input/target shifting, forward-pass shape and finite loss, causal masking, and a parameter-changing optimization step. A short training run then created checkpoints, restored a checkpoint into a new training process, generated a sample, and evaluated held-out loss.

| Check | Result | Evidence |
|---|---|---|
| Unit tests | Passed: 5/5 | `python3 -m unittest discover -s tests -v` |
| Model initialization | Passed | 837,888 trainable parameters on CPU. |
| Training loop | Passed | 8-step run lowered sampled training loss from 5.2427 to 4.7205. |
| Checkpoint creation | Passed | `checkpoints/smoke_step_4.pt` and `checkpoints/smoke_step_8.pt`. |
| Checkpoint restoration | Passed | Restored step-8 checkpoint and continued to step 10. |
| Held-out evaluation | Passed | Checkpoint step 10 reported held-out loss of 4.5737 across two evaluation batches. |
| Text generation | Passed technically | Generation ran successfully; output remained low-quality, as expected for 10 optimization steps on a tiny byte corpus. |

## Metrics observed

| Step | Sampled batch loss | Sampled train loss | Sampled validation loss | Gradient norm |
|---:|---:|---:|---:|---:|
| 1 | 5.5526 | 5.2427 | 5.2199 | 4.672 |
| 4 | 4.9592 | 4.8863 | 4.8628 | 2.726 |
| 8 | 4.7504 | 4.7205 | 4.6694 | 2.592 |
| 10 after restore | 4.6194 | 4.6128 | 4.5890 | 2.628 |

The decreasing sampled losses indicate that the full system can optimize the next-byte prediction objective on the supplied corpus. They do **not** establish meaningful philosophical reasoning, factual reliability, safe behavior, or broad language understanding. The generated text is expected to be weak because the corpus is tiny, the model begins from random initialization, and the validation was purposely kept short.

## Artifacts created

| Artifact | Purpose |
|---|---|
| `outputs/smoke/metrics.jsonl` | Step-wise training and validation records. |
| `outputs/smoke/run_config.json` | Model configuration, training settings, corpus metadata, and parameter count. |
| `checkpoints/smoke_step_8.pt` | Initial end-to-end checkpoint. |
| `checkpoints/resume_smoke_step_10.pt` | Checkpoint produced after restoration and continuation. |
| `outputs/smoke_generation.txt` | Deterministic generated text from the restored checkpoint. |
| `outputs/smoke_evaluation.json` | Checkpoint evaluation output. |

## Next decision

The implementation is ready for a longer controlled smoke run or for a new corpus-ingestion stage. It is **not** ready for public use. Before a 125M-parameter pilot, define the intended users, a source-approval policy, a documented corpus, an explicit evaluation suite, a hardware plan, and a model-release decision process.
