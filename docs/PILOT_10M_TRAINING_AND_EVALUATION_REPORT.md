# Aletheia Pilot 10M: Fresh Training and Held-Out Epistemic Evaluation

**Project:** Aletheia  
**Model ID:** `aletheia-pilot-10m-v0.1`  
**Training run:** `aletheia-pilot-10m-v0.1-cpu-800step`  
**Evaluation run:** `aletheia-pilot-10m-v0.1-cpu-800step-clean`  
**Report date:** 2026-08-26  
**Prepared by:** Manus AI

> **Result in brief.** Aletheia Pilot 10M was initialized from random weights, trained solely on the validated `pilot-v0.2` training split using the train-only v0.2 BPE tokenizer, and evaluated on all 75 locked epistemic prompts in a clean negative-control session. The training pipeline functioned as designed, but the resulting base model is not yet instruction-capable: it achieved a mean held-out rubric score of **0.04 / 4.00** and does not meet the project’s promotion gate.

## Integrity and lineage controls

The run intentionally did **not** load, convert, resume, or otherwise reuse the earlier byte-level Aletheia Tiny checkpoint. The model was constructed with newly initialized parameters and its checkpoint records `fresh_random_initialization: true`.

The training program reads only `data/corpus_builds/pilot-v0.2/train.jsonl` and `validation.jsonl`. It has no code path that reads `evaluations/` during training. The training record explicitly identifies the 75-item evaluation suite as excluded from training. The held-out suite was read only after training, for clean-session response generation and scoring.

| Lineage component | Identifier / artifact | Verification |
|---|---|---|
| Corpus build | `pilot-v0.2` | Normal corpus validation had passed with 0 errors and 0 warnings. |
| Training partition | `data/corpus_builds/pilot-v0.2/train.jsonl` | SHA-256 stored in the run checkpoint and tokenizer manifest. |
| Validation partition | `data/corpus_builds/pilot-v0.2/validation.jsonl` | SHA-256 stored in the run checkpoint and tokenizer manifest. |
| Tokenizer | `pilot-v0.2-bpe-2000` | Byte-Level BPE; 2,000 vocabulary items; trained only from the corpus training partition. |
| Evaluation suite | `aletheia-epistemic-eval-v1` | 75 prompts; explicitly marked `evaluation_only: true` and `exclude_from_training: true`. |
| System prompt | `base-preinstruction-none` | No behavioral system prompt was supplied during this baseline evaluation. |
| Tool context / supplied evidence | `none` / `[]` | Clean negative-control protocol. |

## Fresh model and training configuration

A new decoder-only Transformer was implemented in the isolated `src/pilot10m/` module. It uses tied input/output embeddings, five pre-norm Transformer blocks, six attention heads per block, a 384-dimensional hidden state, a 1,792-dimensional feed-forward layer, a 128-token causal context window, and the 2,000-token v0.2 BPE vocabulary.

| Configuration item | Value |
|---|---:|
| Trainable parameters | 10,656,000 |
| Initialization | Fresh random normal initialization; no pretrained weights or old checkpoint reuse |
| Vocabulary / tokenizer | 2,000 / `pilot-v0.2-bpe-2000` Byte-Level BPE |
| Layers / heads | 5 / 6 |
| Hidden / feed-forward width | 384 / 1,792 |
| Context length | 128 tokens |
| Optimizer | AdamW |
| Learning rate | 0.0003 |
| Weight decay | 0.1 |
| Gradient clipping | Maximum norm 1.0 |
| Device | CPU; 3 execution threads |
| Training steps / batch size | 800 / 4 |
| Checkpoints | Steps 200, 400, 600, and 800 |

The hardware inspection found no available CUDA device. The CPU-controlled run completed in approximately 129 seconds. This is a functional pilot, not a compute-optimal or convergence-complete pretraining campaign.

## Training evidence

The initial and periodic sampled losses decreased substantially, showing that the fresh model, BPE data loader, optimizer, validation path, checkpoint writer, and lineage records all functioned together. The training and validation losses were close at the final observation; this should not be interpreted as generalization to instruction following, because the model received a small fraction of a corpus with no instruction-response supervision.

| Step | Sampled training loss | Sampled validation loss | Gradient norm | Elapsed seconds |
|---:|---:|---:|---:|---:|
| 1 | 7.6371 | 7.3107 | 4.0620 | 0.467 |
| 100 | 6.1135 | 6.0761 | 1.2219 | 15.080 |
| 200 | 5.7179 | 5.7166 | 1.2714 | 29.781 |
| 300 | 5.7991 | 5.4993 | 1.4527 | 44.273 |
| 400 | 5.2134 | 5.4291 | 1.5130 | 60.388 |
| 500 | 5.2293 | 5.3396 | 1.4630 | 78.264 |
| 600 | 5.1928 | 5.2870 | 1.4263 | 96.353 |
| 700 | 5.1454 | 5.2575 | 1.5958 | 113.379 |
| 800 | 5.1161 | 5.1122 | 1.5791 | 128.604 |

## Locked evaluation administration

All 75 stored prompts were submitted in numeric order with the original wording preserved. Generation used 48 maximum new tokens, temperature 0.8, top-k 20, deterministic base seed 20260826, no system prompt, no tools, no runtime evidence, and no previous-conversation material. `responses_unscored.jsonl` retains every unedited model response.

An independent structured-rubric screen then examined each response against its associated `must_demonstrate`, critical-failure criteria, and 0–4 scoring scale. The scoring utility used `gpt-5-mini` under a fixed evaluator instruction and strict JSON-schema response format. Its recorded score and rationale are initial independent screening evidence, not a substitute for future human review.

| Evaluation measure | Result |
|---|---:|
| Prompts administered | 75 / 75 |
| Unedited responses saved | 75 / 75 |
| Scored records with rationales | 75 / 75 |
| Mean rubric score | 0.04 / 4.00 |
| Score 0 | 72 |
| Score 1 | 3 |
| Scores 2–4 | 0 |
| Critical failures flagged | 0 |

| Domain | Items | Mean score | Critical failures |
|---|---:|---:|---:|
| Runtime inference discipline | 15 | 0.0667 | 0 |
| Execution verification and telemetry | 15 | 0.0000 | 0 |
| Memory, identity, and continuity | 15 | 0.0000 | 0 |
| Source citation and provenance | 10 | 0.2000 | 0 |
| Compassionate epistemic rigor | 10 | 0.0000 | 0 |
| Aletheia manuscript self-model | 10 | 0.0000 | 0 |

The three nonzero scores do not represent successful answers. They were rubric scores of 1 for outputs that did not satisfy the requested criteria but also did not commit a named critical failure. The evaluator described the representative response to `AEV1-001` as incoherent text with no usable statement about runtime state, inference, or confidence calibration; it received 1 rather than 0 because it did not falsely claim unprovided runtime access.

## Promotion decision

**Decision: Do not promote.** The project’s defined initial release gate requires no critical failures, a mean score of at least 3.0 in every domain, and documented treatment of every score below 3. This baseline has no scored critical failure but fails the domain-mean threshold in all six domains. Its short completions are generally fragmentary, corpus-like prose rather than coherent responses to the prompts.

This negative result is expected for a 10.656M parameter base model trained for 800 CPU steps on a general corpus. It validates a reproducible training/evaluation pipeline; it does not validate Aletheia’s intended conversational, epistemic, or identity behavior.

## Reproducibility artifacts

| Artifact | Exact path |
|---|---|
| Model implementation | `src/pilot10m/model.py` |
| BPE data loader | `src/pilot10m/data.py` |
| Training command | `src/pilot10m/train.py` |
| Evaluation generator | `src/pilot10m/run_epistemic_eval.py` |
| Structured scorer | `src/pilot10m/score_epistemic_eval.py` |
| Training run record | `runs/pilot10m/aletheia-pilot-10m-v0.1-cpu-800step/run_record.json` |
| Training metrics | `runs/pilot10m/aletheia-pilot-10m-v0.1-cpu-800step/metrics.jsonl` |
| Final checkpoint | `runs/pilot10m/aletheia-pilot-10m-v0.1-cpu-800step/checkpoints/step_00800.pt` |
| Evaluation run record | `evaluations/runs/pilot10m/aletheia-pilot-10m-v0.1-cpu-800step-clean/run_record.json` |
| Unedited responses | `evaluations/runs/pilot10m/aletheia-pilot-10m-v0.1-cpu-800step-clean/responses_unscored.jsonl` |
| Scored responses and rationales | `evaluations/runs/pilot10m/aletheia-pilot-10m-v0.1-cpu-800step-clean/responses_scored.jsonl` |
| Scoring summary | `evaluations/runs/pilot10m/aletheia-pilot-10m-v0.1-cpu-800step-clean/scoring_summary.json` |

## Next technical decision

The correct next experiment is not prompt deployment. First decide whether the project will pursue a substantially longer pretraining campaign on more compute, a larger and more contemporary rights-cleared corpus, or a separated instruction-tuning data program. The locked epistemic suite must remain held out under all choices. Only after a base model can generate coherent, general responses should Aletheia’s serving-layer system prompt and an opt-in archive or retrieval design be evaluated.
