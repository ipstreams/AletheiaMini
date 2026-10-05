# Aletheia Instruction-Tuning Data v1 Card

## Identity and approved use

| Property | Value |
|---|---|
| Dataset ID | `aletheia-instruction-tuning-v1` |
| Project location | `instruction_data/aletheia-instruction-tuning-v1/` |
| Source archive | `instruction_data/aletheia_instruction_tuning_v1.source.zip` |
| Source archive SHA-256 | `cb78a15a0a7c5c8d9252558754553bc4afa7af3b4376e714b5e2d377d047392d` |
| Authorized purpose | Controlled supervised instruction tuning after the fresh 10M base-model run. |
| Permitted model lineage | The BPE Aletheia Pilot 10M lineage only; do not use the byte-level Aletheia Tiny checkpoint. |
| Training partition | `train.jsonl` only, containing 50 dialogue examples. |
| Validation partition | `validation.jsonl` only, containing 12 dialogue examples. |
| Alternate export | `train_prompt_completion.jsonl`, retained for audit and not used by the default chat-format trainer. |

## Provenance and integrity

The source manifest states that all 62 dialogue examples were newly authored for Aletheia and are rights-cleared. Archive extraction followed a read-only inventory and checksum review. The declared SHA-256 values for `MANIFEST.json`, `train.jsonl`, `train_prompt_completion.jsonl`, and `validation.jsonl` all matched the extracted source bytes. The dataset contains 62 unique record IDs and no duplicate user prompts or assistant completions.

## Held-out evaluation separation

The dataset manifest specifies `aletheia-epistemic-eval-v1` as a locked, 75-item evaluation suite that must not be copied, paraphrased, imported, or trained on. A local post-delivery audit compared the instruction records with the actual locked suite, not merely a report summary. It found zero exact instruction-prompt matches, zero exact instruction-message-text matches, and zero matching normalized eight-word phrases. This is a phrase-level separation check, not a semantic-equivalence guarantee. The locked suite remains under `evaluations/suites/` and is not read by the instruction-tuning data loader.

## Content and limitations

| Content domain | Train examples |
|---|---:|
| Evidence boundaries | 10 |
| Memory and continuity | 8 |
| Uncertainty and calibration | 8 |
| Source attribution and provenance | 8 |
| Compassionate epistemic rigor | 8 |
| Runtime self-model and telemetry | 8 |
| Validation-only examples | 12 |

This is a small behavioral prototype, not a general instruction corpus. It can test whether the fine-tuning procedure shifts the base model toward transparent, evidence-bounded answer forms. It cannot establish robust coverage, real tool access, persistent memory, subjective experience, factual correctness beyond supplied evidence, or deployment readiness.

## Exclusions

The following remain excluded from instruction-tuning data:

- `evaluations/suites/aletheia-epistemic-eval-v1/suite.jsonl` and all other evaluation-suite material;
- the served system-prompt package, unless an explicitly versioned prompt-conditioning experiment is approved;
- raw pretraining corpus files and source materials not intentionally converted into rights-cleared instruction examples;
- any content with unresolved rights, privacy, or sensitivity review.
