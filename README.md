# Aletheia Tiny

Aletheia Tiny is a **from-scratch, byte-level decoder-only Transformer** built as the first technical milestone for the Aletheia project. It does not load pretrained weights or an external tokenizer. Its purpose is to verify a complete and traceable language-model training workflow: user-approved input text, causal batching, random initialization, gradient training, evaluation, checkpointing, restoration, and generation.

> **Important limitation:** The included seed corpus is only 8,652 bytes of user-provided philosophical project text. A model trained on it is a systems demonstration, not a reliable assistant, a general LLM, or evidence of consciousness, memory, or moral agency.

## Repository structure

| Path | Purpose |
|---|---|
| `data/raw/aletheia_seed.txt` | Approved seed corpus supplied for this project. |
| `docs/PROJECT_BRIEF.md` | Product intent, behavioral interpretation, and integrity boundaries. |
| `docs/TECHNICAL_SPEC.md` | Versioned architecture and scale-up design. |
| `docs/DATA_CARD.md` | Corpus provenance, checksum, processing, and limitations. |
| `prompts/aletheia_user_submitted_system_prompt_v1.md` | Verbatim user-supplied Aletheia prompt source. |
| `prompts/aletheia_system_prompt_v1_implementable.md` | Transparent, deployable behavioral prompt for a future instruction-capable service. |
| `docs/SYSTEM_PROMPT_REVIEW_V1.md` | Requirement review, tool-protocol boundaries, and validation limits. |
| `docs/MANUSCRIPT_REVIEW.md` | Full-manuscript analysis that grounds Aletheia’s purpose and corpus boundaries. |
| `docs/PILOT_CORPUS_POLICY_V1.md` | Corpus domains, source exclusions, provenance rules, and evaluation criteria. |
| `docs/PILOT_CORPUS_MANIFEST_AND_INGESTION.md` | Manifest contract, source-approval workflow, and corpus-build commands. |
| `docs/CORPUS_AUTHORIZATION_LOG.md` | Explicit permissions recorded for first-party corpus sources. |
| `docs/PILOT_CORPUS_BUILD_STATUS.md` | Current accepted corpus build, split state, and readiness gap. |
| `docs/CORPUS_AUTOMATION_SPEC.md` | Automated validation and tokenizer-training design. |
| `docs/CORPUS_TOOLING_TEST_RESULTS.md` | Validation, diagnostic tokenization, and readiness-gate test results. |
| `docs/EPISTEMIC_EVALUATION_SUITE_DESIGN_V1.md` | Capability map, scoring boundaries, and failure criteria for the held-out benchmark. |
| `docs/EPISTEMIC_EVALUATION_OPERATIONS_V1.md` | Reproducible benchmark-administration and result-recording protocol. |
| `evaluations/suites/aletheia-epistemic-eval-v1/` | Versioned 75-item held-out epistemic evaluation suite and manifest. |
| `corpus/pilot_sources.jsonl` | Versioned source-decision manifest for the pilot corpus. |
| `docs/PILOT_CORPUS_V0_2_REPORT.md` | Normal v0.2 build, validation, source-contribution, tokenizer-lineage, and exclusion report. |
| `data/corpus_builds/pilot-v0.2/` | Training-ready v0.2 corpus, source ledgers, split files, and normal validation report. |
| `data/tokenizers/pilot-v0.2-bpe-2000/` | Train-only 2,000-vocabulary Byte-Level BPE tokenizer and lineage manifest for v0.2. |
| `corpus/source_review/v0_2_deferred_candidates.jsonl` | Auditable ledger of retrieved but non-ingested source candidates. |
| `src/build_pilot_corpus.py` | Approval-gated, deterministic corpus-ingestion builder. |
| `src/validate_corpus.py` | Automated corpus integrity, lineage, split-safety, and readiness validator. |
| `src/train_corpus_tokenizer.py` | Train-only Byte-Level BPE tokenizer utility with recorded lineage. |
| `src/build_epistemic_eval_suite.py` | Reproducibly builds the held-out prompt suite and its scoring metadata. |
| `src/pilot10m/` | Isolated fresh-from-random 10M-class BPE model, training, held-out generation, and structured scoring implementation. |
| `runs/pilot10m/aletheia-pilot-10m-v0.1-cpu-800step/` | Controlled fresh 800-step CPU pilot metrics, lineage records, and checkpoints. |
| `evaluations/runs/pilot10m/aletheia-pilot-10m-v0.1-cpu-800step-clean/` | Clean-session unedited responses and scored 75-item held-out epistemic evaluation record. |
| `docs/PILOT_10M_TRAINING_AND_EVALUATION_REPORT.md` | Complete 10M pilot configuration, provenance, metric, score, rationale, and promotion-decision report. |
| `instruction_data/aletheia-instruction-tuning-v1/` | Verified 50/12 rights-cleared instruction-tuning dataset, checksums, and source manifest. |
| `docs/INSTRUCTION_TUNING_DATA_V1_CARD.md` | Instruction-data provenance, integrity, rights, and locked-evaluation separation record. |
| `src/pilot10m/instruction_data.py` | Checksum-verifying supervised data loader with assistant-completion-only loss masking. |
| `src/pilot10m/finetune_instruction.py` | Isolated validation-selected instruction-tuning trainer for the fresh 10M BPE pilot. |
| `runs/pilot10m/aletheia-pilot-10m-instruction-v1-cpu-30epoch/` | Fine-tuning metrics, selection record, and frozen validation-selected checkpoint. |
| `docs/INSTRUCTION_TUNING_V1_EXPERIMENT_REPORT.md` | Dataset controls, training result, held-out score comparison, and promotion decision. |
| `src/model.py` | Causal decoder-only Transformer implementation. |
| `src/data.py` | Byte-level corpus loading and deterministic sampling. |
| `src/train.py` | Training, logging, checkpoints, and resume support. |
| `src/evaluate.py` | Checkpoint-based train/validation-loss evaluation. |
| `src/generate.py` | Sampled text generation from a checkpoint. |
| `tests/` | Unit tests for data, masking, forward pass, and optimization. |

## Installation

Create an isolated Python environment if desired, then install the declared dependency.

```bash
pip3 install -r requirements.txt
```

## Verify the implementation

Run the unit-test suite before training. It checks corpus loading, causal target shifting, model shapes, causal masking, and a complete optimization step.

```bash
python3 -m unittest discover -s tests -v
```

## Run a smoke training job

The following command performs a short verification run on CPU. It creates structured metrics under `outputs/smoke/` and checkpoints under `checkpoints/`.

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

For an accelerator-enabled environment, use `--device cuda` after verifying that PyTorch detects the device. Do not interpret lower loss on the tiny seed corpus as broad capability; it mainly indicates that the code can learn local byte patterns.

## Resume from a checkpoint

A training checkpoint stores the model state, optimizer state, model and training configuration, corpus metadata, step counter, and PyTorch random-number-generator state.

```bash
python3 src/train.py \
  --run-name continuation \
  --resume checkpoints/smoke_step_100.pt \
  --steps 200 \
  --batch-size 8 \
  --device cpu
```

## Evaluate a checkpoint

```bash
python3 src/evaluate.py \
  --checkpoint checkpoints/smoke_step_100.pt \
  --batches 20 \
  --batch-size 8 \
  --device cpu
```

## Generate a sample

```bash
python3 src/generate.py \
  --checkpoint checkpoints/smoke_step_100.pt \
  --prompt "Aletheia: " \
  --tokens 160 \
  --temperature 0.8 \
  --top-k 32 \
  --device cpu
```

## Prompt-layer status

The prompt package defines Aletheia’s intended interaction behavior, including first-person transparency, consent-based journal retrieval, and disclosed lookup requests. It is **not active in Aletheia Tiny**: the current 100-step byte-level checkpoint cannot reliably follow language instructions. Apply the implementable prompt only after moving to an instruction-capable model and a host application that validates every memory or lookup protocol.

## Scale-up path

The correct next research milestone is not immediate public deployment. First build a lawful, auditable corpus and train a 125M-parameter pilot using the same checkpointing and evaluation discipline. Replace the byte tokenizer with a tokenizer trained only on approved corpus text, retain explicit data manifests, add a private held-out evaluation suite, and validate checkpoint restoration and throughput at the larger scale. A persistent memory or reflective dialogue layer, if later added, must be opt-in and must not be described as proof that the model experiences continuity or has a subjective self.
