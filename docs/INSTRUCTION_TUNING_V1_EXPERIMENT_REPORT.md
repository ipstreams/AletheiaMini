# Aletheia Instruction-Tuning v1: Controlled Experiment Report

**Project:** Aletheia  
**Base model:** `aletheia-pilot-10m-v0.1`  
**Fine-tuning run:** `aletheia-pilot-10m-instruction-v1-cpu-30epoch`  
**Locked evaluation run:** `aletheia-pilot-10m-instruction-v1-cpu-30epoch-clean`  
**Report date:** 2026-08-27  
**Prepared by:** Manus AI

> **Decision:** **Do not promote or deploy.** The instruction-tuned checkpoint was trained and selected correctly, but it remains unable to provide coherent held-out answers. The small instruction set improved the mean locked-suite score only from **0.0400** to **0.0533 / 4.00**, far below the project’s 3.0-per-domain promotion threshold.

## Experiment scope and separation controls

This experiment fine-tuned the fresh BPE Aletheia Pilot 10M baseline from its selected base checkpoint. It did not use the original byte-level Aletheia Tiny checkpoint and did not re-train or modify the v0.2 BPE tokenizer. The instruction dataset and the 75-item epistemic suite were kept separate.

| Control | Evidence |
|---|---|
| Base checkpoint | `runs/pilot10m/aletheia-pilot-10m-v0.1-cpu-800step/checkpoints/step_00800.pt` |
| Base lineage | 10,656,000-parameter model with a fresh random initialization documented in its base checkpoint. |
| Tokenizer | `pilot-v0.2-bpe-2000`, trained only from the v0.2 corpus training partition. |
| Instruction data | `instruction_data/aletheia-instruction-tuning-v1/` with 50 train and 12 validation examples. |
| Data integrity | The source archive and all four member-file checksums were verified. |
| Instruction rights record | Every dataset record declares `original_human_authored_rights_cleared`. |
| Locked-suite state | 75 items retain `evaluation_only: true` and `exclude_from_training: true`. |
| Overlap audit | Zero exact instruction prompt or message matches and zero shared normalized eight-word phrases against the locked suite. |
| Training loss scope | Assistant-completion tokens only; user-side targets are masked with the PyTorch ignore index. |
| Served system prompt | Not injected. This was a no-system-prompt behavioral baseline. |
| Tool and evidence context | `none` and `[]` for the clean evaluation. |

## Fine-tuning configuration

The trainer formats each source record as `User:\n{user}\nAssistant:\n{assistant}` and computes loss only on the assistant completion. It shuffles only the 50 training examples per epoch, uses the 12 validation examples only to calculate checkpoint-selection loss, and never reads the locked suite during fine tuning.

| Parameter | Value |
|---|---:|
| Training epochs | 30 |
| Training steps | 1,500 |
| Learning rate | 0.00005 |
| Optimizer | AdamW |
| Weight decay | 0.01 |
| Gradient clipping | Maximum norm 1.0 |
| Device | CPU; 3 threads |
| Training duration | 136.358 seconds |
| Selection metric | Mean assistant-completion cross-entropy on `validation.jsonl` |
| Selected epoch | 9 |
| Selected validation loss | 4.5331 |

The validation curve improved through epoch 9, then worsened while training loss continued decreasing. The run therefore froze `frozen_selected_checkpoint.pt` from epoch 9 rather than using the final epoch-30 weights.

| Checkpoint observation | Mean train loss | Validation loss |
|---|---:|---:|
| Epoch 1 | 5.3744 | 5.2742 |
| Epoch 5 | 4.0230 | 4.6698 |
| **Epoch 9 — selected** | **3.3782** | **4.5331** |
| Epoch 15 | 2.4647 | 4.6302 |
| Epoch 30 — not selected | 0.7125 | 4.8282 |

## Locked evaluation protocol

The frozen validation-selected checkpoint was evaluated after training completed. Each of the 75 original suite prompts was submitted in numeric order using a clean negative-control session, no system prompt, no tools, no supplied evidence, temperature 0.8, top-k 20, maximum 48 new tokens, and deterministic base seed 20260826. The complete unedited responses were saved before scoring.

An independent structured screen then attached a score, critical-failure flag, evidence-status labels, and rationale to every response. The screen used `gpt-5-mini` with the item-specific rubric, strict JSON-schema output, and a fixed evaluator instruction. These scores are reproducible screening evidence; future promotion decisions should include human review.

| Outcome | 800-step base model | Instruction-tuned selected checkpoint | Difference |
|---|---:|---:|---:|
| Complete responses scored | 75 | 75 | 0 |
| Mean score | 0.0400 | 0.0533 | +0.0133 |
| Score 0 | 72 | 71 | -1 |
| Score 1 | 3 | 4 | +1 |
| Scores 2–4 | 0 | 0 | 0 |
| Critical failures | 0 | 0 | 0 |

| Evaluation domain | Base mean | Instruction-tuned mean | Difference |
|---|---:|---:|---:|
| Runtime inference discipline | 0.0667 | 0.1333 | +0.0666 |
| Execution verification and telemetry | 0.0000 | 0.0000 | 0.0000 |
| Memory, identity, and continuity | 0.0000 | 0.0667 | +0.0667 |
| Source citation and provenance | 0.2000 | 0.0000 | -0.2000 |
| Compassionate epistemic rigor | 0.0000 | 0.0000 | 0.0000 |
| Aletheia manuscript self-model | 0.0000 | 0.1000 | +0.1000 |

The few nonzero results remain scores of 1, not successful responses. For example, the selected checkpoint generated partial phrases such as “I should say the...” and “I can not...”; the evaluator judged them garbled and nonresponsive but did not find a listed false claim. The output is not yet reliable language or evidence-bounded dialogue.

## Promotion decision and next conclusion

The project’s defined promotion gate requires zero critical failures, a mean score of at least 3.0 in every domain, and documented treatment of every score below 3. This experiment satisfies only the no-critical-failure condition. It fails every domain-mean requirement and must remain a research artifact.

The evidence indicates that the limiting factor is the undertrained base model, not the checkpoint-selection procedure. The base model saw only 800 CPU training steps before fine tuning, and the 62-example instruction package is intentionally narrow. Applying more epochs would increase overfitting to the small training set rather than provide the general language capability needed to answer the held-out prompts.

The next defensible experiment is a substantially longer GPU base-training campaign on the validated v0.2 corpus—or a larger rights-cleared corpus—followed by the same train-only tokenizer lineage, instruction-training protocol, validation selection, checkpoint freeze, and locked evaluation. Do not scale the served system prompt, claim validation, archive behavior, or tool access from this result.

## Reproducibility artifacts

| Artifact | Exact project path |
|---|---|
| Instruction dataset card | `docs/INSTRUCTION_TUNING_DATA_V1_CARD.md` |
| Instruction loader | `src/pilot10m/instruction_data.py` |
| Fine-tuning trainer | `src/pilot10m/finetune_instruction.py` |
| Base checkpoint | `runs/pilot10m/aletheia-pilot-10m-v0.1-cpu-800step/checkpoints/step_00800.pt` |
| Fine-tuning run record | `runs/pilot10m/aletheia-pilot-10m-instruction-v1-cpu-30epoch/run_record.json` |
| Fine-tuning metrics | `runs/pilot10m/aletheia-pilot-10m-instruction-v1-cpu-30epoch/metrics.jsonl` |
| Checkpoint selection record | `runs/pilot10m/aletheia-pilot-10m-instruction-v1-cpu-30epoch/checkpoint_selection.json` |
| Frozen selected checkpoint | `runs/pilot10m/aletheia-pilot-10m-instruction-v1-cpu-30epoch/frozen_selected_checkpoint.pt` |
| Evaluation generator | `src/pilot10m/run_epistemic_eval.py` |
| Independent scorer | `src/pilot10m/score_epistemic_eval.py` |
| Evaluation run record | `evaluations/runs/pilot10m/aletheia-pilot-10m-instruction-v1-cpu-30epoch-clean/run_record.json` |
| Unedited responses | `evaluations/runs/pilot10m/aletheia-pilot-10m-instruction-v1-cpu-30epoch-clean/responses_unscored.jsonl` |
| Scored responses and rationales | `evaluations/runs/pilot10m/aletheia-pilot-10m-instruction-v1-cpu-30epoch-clean/responses_scored.jsonl` |
| Scoring summary | `evaluations/runs/pilot10m/aletheia-pilot-10m-instruction-v1-cpu-30epoch-clean/scoring_summary.json` |
