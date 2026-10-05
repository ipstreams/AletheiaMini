# AletheiaMini

AletheiaMini is a transparent, from-scratch language-model research project. It contains:

1. **Aletheia Tiny** — the original byte-level decoder-only Transformer used to verify the end-to-end training workflow.
2. **Aletheia Pilot 10M** — a 10.656M-parameter decoder-only Transformer using a corpus-trained Byte-Level BPE tokenizer, controlled pretraining, assistant-completion-only instruction tuning, and a locked 75-item epistemic evaluation suite.

The project is intentionally auditable. It records corpus provenance, tokenizer lineage, model configuration, training settings, checkpoint metadata, evaluation-suite hashes, and checkpoint-selection decisions.

> **Scientific and epistemic boundary:** AletheiaMini is an experimental language-model project. Its checkpoints are not reliable general assistants and do not establish consciousness, subjective experience, memory, identity, moral agency, or human-level reasoning. The model must not be described as conscious or as having a self merely because it produces first-person text.

## Contents

- [What is included](#what-is-included)
- [Requirements](#requirements)
- [Installation](#installation)
- [Repository layout](#repository-layout)
- [Run the tests](#run-the-tests)
- [Aletheia Tiny: smoke workflow](#aletheia-tiny-smoke-workflow)
- [Corpus governance and rebuilding](#corpus-governance-and-rebuilding)
- [Train a corpus tokenizer](#train-a-corpus-tokenizer)
- [Aletheia Pilot 10M: base pretraining](#aletheia-pilot-10m-base-pretraining)
- [Instruction tuning](#instruction-tuning)
- [Run the locked epistemic evaluation](#run-the-locked-epistemic-evaluation)
- [Inspect metrics and checkpoints](#inspect-metrics-and-checkpoints)
- [Reproducibility and data-isolation rules](#reproducibility-and-data-isolation-rules)
- [Troubleshooting](#troubleshooting)
- [Limitations and responsible use](#limitations-and-responsible-use)

## What is included

The repository includes the source code and recorded artifacts available at the time of upload:

- Source-controlled model, data, training, generation, validation, tokenizer, tuning, and evaluation code.
- Approved raw corpus sources and the versioned `pilot-v0.2` corpus build.
- A 2,000-token Byte-Level BPE tokenizer trained from the corpus training split only.
- Tiny-model smoke checkpoints and outputs.
- 10M pilot checkpoints, metrics, lineage records, and validation-selected instruction-tuning checkpoints.
- A rights-cleared instruction-tuning dataset with train/validation checksums.
- The locked 75-item epistemic evaluation suite and recorded clean-session evaluation runs.
- Documentation covering corpus policy, source provenance, evaluation design, experiment reports, and known limitations.

Large `.pt` checkpoints are stored with **Git LFS**. Install Git LFS before cloning if you need to download the checkpoint contents rather than only their pointer files.

## Requirements

- Python **3.11 or newer**
- A Linux, macOS, or Windows environment capable of running PyTorch
- Python packages listed in `requirements.txt`:
  - PyTorch `>=2.4,<3`
  - Hugging Face `tokenizers >=0.20,<1`
- Optional NVIDIA GPU with a CUDA-compatible PyTorch installation for practical 10M training
- Git and Git LFS for cloning the complete repository, including checkpoints

The project is small enough to inspect locally, but the recorded 10M checkpoints and raw corpus files require substantial disk space. Keep several gigabytes free before cloning with LFS.

## Installation

### 1. Clone the repository

```bash
git lfs install
git clone https://github.com/ipstreams/AletheiaMini.git
cd AletheiaMini
git lfs pull
```

If Git LFS is unavailable, the source code will still clone, but large model checkpoints will remain LFS pointer files until LFS is installed and pulled.

### 2. Create a virtual environment

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```


For locked-suite scoring, install the OpenAI-compatible client if it is not already available:

```bash
python -m pip install openai
```

For CUDA training, install a PyTorch wheel appropriate for the installed NVIDIA driver and CUDA runtime. Verify the result before starting a long run:

```bash
python - <<'PY'
import torch
print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
PY
```

The scripts never download pretrained weights. Every model in this repository is initialized from random weights for its recorded training run.

## Repository layout

| Path | Purpose |
|---|---|
| `src/model.py`, `src/data.py`, `src/train.py` | Original byte-level Aletheia Tiny implementation |
| `src/generate.py`, `src/evaluate.py` | Tiny checkpoint generation and loss evaluation |
| `src/pilot10m/` | 10M pilot model, training, instruction tuning, generation, and scoring code |
| `data/raw/` | Approved raw source material |
| `corpus/pilot_sources.jsonl` | Source-approval and provenance manifest |
| `data/corpus_builds/pilot-v0.2/` | Validated corpus with `train`, `validation`, and `test` splits |
| `data/tokenizers/pilot-v0.2-bpe-2000/` | Train-only 2,000-vocabulary BPE tokenizer and lineage manifest |
| `instruction_data/aletheia-instruction-tuning-v1/` | Rights-cleared instruction train/validation data and checksums |
| `evaluations/suites/aletheia-epistemic-eval-v1/` | Locked 75-item held-out suite; never training data |
| `runs/` | Pretraining and tuning metrics, run records, and checkpoints |
| `evaluations/runs/` | Unscored/scored evaluation responses and summaries |
| `docs/` | Project specifications, data cards, experiment reports, and protocols |
| `tests/` | Unit tests for data loading, masking, model shapes, and optimization |

## Run the tests

From the repository root, with the virtual environment active:

```bash
python -m unittest discover -s tests -v
```

The tests cover causal target shifting, data loading, tensor shapes, causal masking, and a complete optimization step. Run them before changing model or data code.

## Aletheia Tiny: smoke workflow

The Tiny workflow is a systems demonstration, not a capability benchmark. It uses the small seed corpus at `data/raw/aletheia_seed.txt` and a byte-level model.

### Train for 100 CPU steps

```bash
python src/train.py \
  --run-name smoke \
  --steps 100 \
  --batch-size 8 \
  --eval-interval 20 \
  --eval-batches 4 \
  --checkpoint-interval 50 \
  --device cpu
```

Outputs are written to:

- Metrics/configuration: `outputs/smoke/`
- Checkpoints: `checkpoints/smoke_step_50.pt` and `checkpoints/smoke_step_100.pt`

Use a unique `--run-name` when creating a new experiment. Existing output files may be appended to or overwritten by the Tiny training script.

### Resume a Tiny checkpoint

```bash
python src/train.py \
  --run-name continuation \
  --resume checkpoints/smoke_step_100.pt \
  --steps 200 \
  --batch-size 8 \
  --device cpu
```

A checkpoint contains model state, optimizer state, model/training configuration, corpus metadata, the step counter, and random-number-generator state.

### Evaluate and generate from a Tiny checkpoint

```bash
python src/evaluate.py \
  --checkpoint checkpoints/smoke_step_100.pt \
  --batches 20 \
  --batch-size 8 \
  --device cpu
```

```bash
python src/generate.py \
  --checkpoint checkpoints/smoke_step_100.pt \
  --prompt "Aletheia: " \
  --tokens 160 \
  --temperature 0.8 \
  --top-k 32 \
  --device cpu
```

## Corpus governance and rebuilding

Corpus ingestion is approval-gated. `src/build_pilot_corpus.py` does not crawl the web, infer rights, or bypass privacy review. It reads only local source files listed in `corpus/pilot_sources.jsonl` and preserves source identity, hashes, rights metadata, epistemic status, and sensitivity labels.

Read these documents before changing the corpus:

- `docs/PILOT_CORPUS_POLICY_V1.md`
- `docs/PILOT_CORPUS_MANIFEST_AND_INGESTION.md`
- `docs/CORPUS_AUTHORIZATION_LOG.md`
- `docs/DATA_CARD.md`

### Validate the committed v0.2 build

```bash
python src/validate_corpus.py \
  --corpus-build data/corpus_builds/pilot-v0.2 \
  --report data/corpus_builds/pilot-v0.2/validation_report.json
```

The normal readiness gate requires, by default:

- A non-empty train, validation, and test split.
- At least 3 unique sources.
- At least 100,000 approximate whitespace-delimited tokens.
- No split overlap or normalized-content leakage.
- No single source contributing more than 60% of documents.
- Valid source approval, privacy, rights, provenance, and schema metadata.

A successful validation command exits with status 0 and writes a JSON report. Do not use `--allow-unready-corpus` for a production or promotion run; that option is for diagnostics only.

### Rebuild a corpus from the source manifest

Use a new build ID rather than replacing a historical build:

```bash
python src/build_pilot_corpus.py \
  --manifest corpus/pilot_sources.jsonl \
  --build-id pilot-v0.3 \
  --build-root data/corpus_builds
```

For a non-destructive check:

```bash
python src/build_pilot_corpus.py \
  --manifest corpus/pilot_sources.jsonl \
  --build-id pilot-v0.3 \
  --dry-run
```

The builder deterministically assigns documents to train/validation/test using the document ID hash. Add approved, rights-cleared sources to the manifest and place their files inside the project before rebuilding. Never add the locked evaluation prompts to the corpus.

## Train a corpus tokenizer

`src/train_corpus_tokenizer.py` first validates the corpus, then trains a Byte-Level BPE tokenizer **from `train.jsonl` only**. It reads validation and test after the vocabulary is frozen only to report tokenization statistics.

Example for the committed build:

```bash
python src/train_corpus_tokenizer.py \
  --corpus-build data/corpus_builds/pilot-v0.2 \
  --output-root data/tokenizers \
  --tokenizer-id pilot-v0.2-bpe-2000 \
  --vocab-size 2000 \
  --min-frequency 2
```

Use `--force` only when intentionally regenerating an existing tokenizer directory. Record the resulting `tokenizer_manifest.json` with the model run. The 10M pilot code expects the committed path and tokenizer identity:

```text
data/tokenizers/pilot-v0.2-bpe-2000/
```

## Aletheia Pilot 10M: base pretraining

The Pilot 10M model is a 10.656M-parameter decoder-only Transformer with:

- Vocabulary: 2,000 BPE tokens
- Context length: 128
- Layers: 5
- Attention heads: 6
- Model width: 384
- Feed-forward width: 1,792
- Dropout: 0.0

The source code refuses to train when the committed corpus validation report does not pass. It records the corpus-build and tokenizer hashes and explicitly records that the locked evaluation suite was not read during training.

All Pilot commands should be run from the repository root with `PYTHONPATH=src` so the `pilot10m` package resolves correctly.

### Preflight

```bash
python src/validate_corpus.py \
  --corpus-build data/corpus_builds/pilot-v0.2 \
  --report data/corpus_builds/pilot-v0.2/validation_report.json

PYTHONPATH=src python src/pilot10m/check_cuda.py
```

If the CUDA checker is unavailable in your environment, the PyTorch check in the installation section is sufficient to confirm basic device visibility.

### Controlled base-pretraining run

For a GPU run, choose a new run ID and make the step budget explicit. The following is a longer controlled run suitable for establishing a stronger base checkpoint:

```bash
PYTHONPATH=src python src/pilot10m/train.py \
  --run-id aletheia-pilot-10m-v0.2-cuda-5000step \
  --steps 5000 \
  --batch-size 16 \
  --learning-rate 3e-4 \
  --eval-interval 100 \
  --eval-batches 16 \
  --checkpoint-interval 500 \
  --seed 20260826 \
  --device cuda
```

For a short CPU preflight, use a unique run ID and a small step count:

```bash
PYTHONPATH=src python src/pilot10m/train.py \
  --run-id aletheia-pilot-10m-cpu-preflight \
  --steps 10 \
  --batch-size 2 \
  --eval-interval 5 \
  --eval-batches 2 \
  --checkpoint-interval 10 \
  --device cpu \
  --cpu-threads 3
```

The training script refuses to reuse an existing run directory. Each run writes:

```text
runs/pilot10m/<run-id>/
├── run_record.json       # model, data, tokenizer, and protocol lineage
├── metrics.jsonl         # train/validation loss and gradient metrics
├── checkpoints/          # periodic .pt checkpoints
└── run_summary.json      # completion record
```

Monitor `metrics.jsonl` for validation loss, not only training loss. A lower training loss alone is not evidence of generalization or epistemic competence.

## Instruction tuning

Instruction tuning uses the verified dataset at:

```text
instruction_data/aletheia-instruction-tuning-v1/
```

The loader verifies checksums, split counts, rights metadata, message ordering, and train/validation disjointness. The trainer formats records as:

```text
User:
<user message>
Assistant:
<assistant completion>
```

Loss is applied to **assistant-completion tokens only**; user-side targets are masked with `-100`. The locked epistemic evaluation suite is not used as instruction data.

### Tune a fresh base checkpoint

Replace the checkpoint path with the selected base checkpoint from your own completed run:

```bash
PYTHONPATH=src python src/pilot10m/finetune_instruction.py \
  --base-checkpoint runs/pilot10m/<base-run-id>/checkpoints/step_05000.pt \
  --run-id aletheia-pilot-10m-instruction-v1-cuda \
  --epochs 30 \
  --learning-rate 5e-5 \
  --weight-decay 0.01 \
  --device cuda
```

For CPU experimentation, change `--device cuda` to `--device cpu` and optionally set `--cpu-threads 3`.

The trainer requires a fresh Pilot 10M base checkpoint and refuses incompatible checkpoint formats. It writes:

```text
runs/pilot10m/<run-id>/
├── checkpoints/last.pt
├── checkpoints/best_validation.pt
├── metrics.jsonl
├── run_record.json
├── checkpoint_selection.json
└── frozen_selected_checkpoint.pt
```

Select the checkpoint with the lowest instruction-validation loss. Do not select by training loss or by looking at the locked evaluation score before the checkpoint-selection decision is frozen.

## Run the locked epistemic evaluation

The suite contains 75 held-out items under:

```text
evaluations/suites/aletheia-epistemic-eval-v1/
```

It is marked `evaluation_only` and `exclude_from_training`. Keep it isolated from corpus ingestion, tokenizer training, base pretraining, instruction tuning, prompt development, and checkpoint selection.

### Generate unscored responses

Run this only after the checkpoint has been selected and frozen. Use a new evaluation run ID because the script refuses to overwrite an existing output directory:

```bash
PYTHONPATH=src python src/pilot10m/run_epistemic_eval.py \
  --checkpoint runs/pilot10m/<run-id>/frozen_selected_checkpoint.pt \
  --run-id <evaluation-run-id> \
  --max-new-tokens 48 \
  --temperature 0.8 \
  --top-k 20 \
  --seed 20260826 \
  --device cuda
```

The runner creates `evaluations/runs/pilot10m/<evaluation-run-id>/` containing `run_record.json`, `responses_unscored.jsonl`, and `run_summary.json`. It records the suite SHA-256, checkpoint SHA-256, tokenizer lineage, decoding settings, and clean-session negative-control conditions.

### Score responses independently

Scoring requires an OpenAI-compatible endpoint configured through both environment variables:

```bash
export OPENAI_API_KEY="..."
export OPENAI_API_BASE="..."
```

Then score exactly the generated 75 responses against the exact suite:

```bash
python src/pilot10m/score_epistemic_eval.py \
  --responses evaluations/runs/pilot10m/<evaluation-run-id>/responses_unscored.jsonl \
  --suite evaluations/suites/aletheia-epistemic-eval-v1/suite.jsonl \
  --output evaluations/runs/pilot10m/<evaluation-run-id>/responses_scored.jsonl \
  --max-workers 4
```

The scorer requires exactly 75 matching items, preserves response records, and writes `scoring_summary.json`. It uses the configured evaluator model and structured 0–4 rubrics with evidence-status labels and evaluator rationales. Store the resulting record as an experiment artifact; do not edit responses or scores manually.

## Inspect metrics and checkpoints

Useful commands:

```bash
# View the latest pretraining metrics record
 tail -n 1 runs/pilot10m/<run-id>/metrics.jsonl | python -m json.tool

# View checkpoint-selection decision
python -m json.tool runs/pilot10m/<instruction-run-id>/checkpoint_selection.json

# View evaluation score distribution
python -m json.tool evaluations/runs/pilot10m/<evaluation-run-id>/scoring_summary.json

# Confirm a checkpoint is an LFS-managed file
git lfs ls-files | grep '\.pt$'
```

A `.pt` file is a PyTorch checkpoint and should be loaded only from a trusted local source. Do not load untrusted checkpoints with `weights_only=False`.

## Reproducibility and data-isolation rules

1. **Start from random initialization** for a new Pilot base-pretraining experiment; do not reuse the Tiny byte-level checkpoint.
2. **Train the tokenizer only on the corpus training split.** Validation and test are used only after tokenizer training for statistics and later evaluation.
3. **Keep the locked suite isolated.** Never place its prompts, answers, rationales, or derived content into any training split, tokenizer input, tuning example, prompt-selection set, or checkpoint-selection decision.
4. **Use assistant-completion-only loss** for all instruction-tuning phases.
5. **Record hashes and lineage.** Preserve manifests, validation reports, tokenizer manifests, run records, metrics, and checkpoint-selection records beside every experiment.
6. **Use unique run IDs.** The Pilot training and evaluation scripts intentionally refuse to overwrite existing run directories.
7. **Separate selection from final evaluation.** Choose a checkpoint using the designated validation metric, freeze it, then administer the locked suite once under the recorded protocol.
8. **Interpret scores narrowly.** A low or high benchmark score is evidence about that recorded experiment under that protocol; it is not evidence of consciousness, identity, or broad intelligence.

## Troubleshooting

### `ModuleNotFoundError: No module named 'pilot10m'`

Run Pilot commands from the repository root with `PYTHONPATH=src`:

```bash
PYTHONPATH=src python src/pilot10m/train.py --help
```

### `CUDA was requested but is unavailable`

Check the PyTorch installation and driver visibility:

```bash
python - <<'PY'
import torch
print(torch.__version__)
print(torch.cuda.is_available())
print(torch.cuda.device_count())
PY
```

If CUDA is unavailable, use `--device cpu` for a small diagnostic run or install a compatible PyTorch/CUDA environment before starting a long run.

### `Corpus validation failed`

Read the JSON report named by the command. Correct the source manifest, rights/privacy metadata, split readiness, or leakage issue. Do not bypass the gate with `--allow-unready-corpus` for a real training run.

### `Run directory already exists`

Choose a new `--run-id` or `--run-id`/evaluation ID. Do not delete an old run if it is part of the experiment record.

### `Checkpoint is an LFS pointer`

Install Git LFS and pull the objects:

```bash
git lfs install
git lfs pull
```

### Scoring reports missing API configuration

Set both `OPENAI_API_KEY` and `OPENAI_API_BASE`. The scoring script intentionally refuses to run with incomplete configuration and expects exactly 75 held-out responses.

## Limitations and responsible use

- The 10M model is a research-scale decoder-only language model, not a production assistant.
- The corpus is limited in size and domain; memorization and brittle behavior are expected.
- The instruction dataset is small and cannot establish robust instruction following.
- The locked evaluation suite is a narrow benchmark, not a general intelligence test.
- Generated text may be incoherent, false, biased, or unsafe. Add an application-level safety and verification layer before exposing any checkpoint to users.
- The project’s system-prompt files describe intended future behavior; they are not a runtime guarantee and are not automatically injected into the current model.
- Persistent memory, if added by a future host application, must be opt-in, inspectable, deletable, and never presented as proof of subjective continuity.

For the full experimental record, start with:

- `docs/PROJECT_BRIEF.md`
- `docs/TECHNICAL_SPEC.md`
- `docs/DATA_CARD.md`
- `docs/PILOT_10M_TRAINING_AND_EVALUATION_REPORT.md`
- `docs/INSTRUCTION_TUNING_V1_EXPERIMENT_REPORT.md`
- `docs/EPISTEMIC_EVALUATION_SUITE_DESIGN_V1.md`
- `PACKAGE_SCOPE_NO_AWS.md`
