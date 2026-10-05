# Aletheia Pilot Corpus Manifest and Ingestion Pipeline

## Purpose and current state

This package turns Aletheia’s manuscript-grounded corpus policy into a reproducible local pipeline. It is designed to protect the distinctions the manuscript depends on: **record versus memory, hypothesis versus evidence, metaphor versus mechanism, and inheritance versus undocumented continuity**.

The pipeline is intentionally conservative. It ingests only local text files listed in a manifest, never discovers sources on its own, never infers rights, never silently processes a quarantined source, and never treats a successful script run as evidence that the corpus is ready to train.

The initial manifest contains one previously approved technical smoke-test source and two excluded references. Its diagnostic result is expected to be `training_ready: false`: one document cannot populate a robust train, validation, and test split. The manifest is a working template, not a claim that the pilot corpus already exists.

## Project layout

```text
aletheia/
├── corpus/
│   ├── pilot_sources.jsonl                # One source-decision record per line
│   └── schemas/
│       └── source_record.schema.json      # Contract for a source record
├── data/
│   ├── raw/                               # Approved or review-pending original text files
│   ├── source_review/                     # Review-only material; never train by default
│   └── corpus_builds/
│       └── <build-id>/                    # Immutable generated corpus build
├── docs/
│   ├── MANUSCRIPT_REVIEW.md
│   ├── PILOT_CORPUS_POLICY_V1.md
│   └── PILOT_CORPUS_MANIFEST_AND_INGESTION.md
└── src/
    └── build_pilot_corpus.py              # Deterministic ingestion program
```

Raw source files are not edited by the builder. Normalization and derived JSONL output are written only to a new build directory. This makes it possible to reproduce or remove a corpus build without losing the original artifact or its decision history.

## Source-record contract

Each line of `corpus/pilot_sources.jsonl` is a JSON object describing one source file and its eligibility. The full machine-checkable contract is in `corpus/schemas/source_record.schema.json`.

| Field group | Required fields | Purpose |
|---|---|---|
| Identity | `source_id`, `title`, `source_path` | Gives the source a stable lineage and locates the local raw artifact. |
| Rights | `source_type`, `rights_basis`, optional `rights_evidence` | Records why the source may be considered for training. |
| Meaning | `content_domain`, `epistemic_status`, `human_or_model_origin` | Preserves whether material is narrative, a record, a hypothesis, or a technical explanation. |
| Sensitivity | `sensitivity_tags`, `privacy_review` | Makes high-risk content visible before it is included. |
| Approval gate | `training_use_approved`, `review_status`, `include_in_pilot` | Prevents accidental ingestion of pending or rejected material. |
| Reproducibility | `source_sha256` | Detects when a file changed after its review decision. |

A source becomes eligible only when all of the following are true:

```text
training_use_approved == true
review_status == "approved"
include_in_pilot == true
privacy_review in {"passed", "not_required"}
```

All other records are written to the generated `excluded_sources.jsonl` ledger with their actual gating values. They are not opened, copied, or normalized by the ingestion process.

## Adding a source: required review sequence

1. Place the original, approved file under `data/raw/` using a stable, descriptive filename. Do not overwrite an existing file after approval; create a new versioned filename instead.
2. Confirm the use basis. The record must name a clear license, a public-domain basis, or an explicit permission record. “Found online” is not a use basis.
3. Review privacy and sensitivity. Private conversations, personal identifiers, and highly sensitive material remain quarantined unless there is a documented decision to include them.
4. Assign the source’s domain, epistemic status, and origin. For material that mixes narrative with technical hypotheses, use `mixed` rather than erasing the distinction.
5. Compute the SHA-256 hash and add a JSON object to `corpus/pilot_sources.jsonl`.
6. Run a dry validation. Fix all errors before building output.
7. Review the generated acceptance and exclusion ledgers. Only then create a build directory.

A minimal approved record has this shape:

```json
{
  "source_id": "example_public_domain_essay_v1",
  "title": "Example Public-Domain Essay",
  "source_path": "data/raw/example_public_domain_essay_v1.txt",
  "source_type": "public_domain",
  "rights_basis": "Public-domain verification recorded in project source memo.",
  "content_domain": "philosophy_ethics_epistemology",
  "epistemic_status": "opinion",
  "human_or_model_origin": "human",
  "sensitivity_tags": ["none"],
  "privacy_review": "not_required",
  "training_use_approved": true,
  "review_status": "approved",
  "include_in_pilot": true,
  "source_sha256": "replace-with-64-character-sha256",
  "notes": "Describe edition, collection date, and review decision."
}
```

## Ingestion pipeline

The builder performs the following deterministic sequence.

| Stage | Action | Output or control |
|---|---|---|
| 1. Parse | Reads JSONL source records and validates required controlled values. | Fails on malformed records, unknown categories, or duplicate source IDs. |
| 2. Gate | Applies the rights, review, privacy, and inclusion conditions. | Writes ineligible source decisions to an exclusion ledger; does not read their content. |
| 3. Verify | Resolves approved paths inside the project and verifies the source hash when declared. | Fails if an approved file is missing, altered, or points outside the project. |
| 4. Normalize | Decodes UTF-8 with counted replacements, converts Unicode to NFC, standardizes line endings, and removes control characters. | Produces normalized text and a normalized-content hash. |
| 5. Deduplicate | Compares normalized hashes. | Excludes exact normalized duplicates and retains the decision. |
| 6. Split | Assigns each document to train, validation, or test by a stable hash of its document ID. | Keeps source documents together; avoids content fragments crossing splits. |
| 7. Audit | Writes source and build metadata alongside corpus output. | Produces a reproducible lineage record. |
| 8. Readiness check | Rejects empty train, validation, or test splits by default. | Prevents a diagnostic build from being mistaken for trainable data. |

## Commands

Run all commands from the Aletheia project directory.

```bash
cd /home/ubuntu/aletheia
```

Validate the manifest without writing files:

```bash
python3 src/build_pilot_corpus.py \
  --manifest corpus/pilot_sources.jsonl \
  --build-id pilot-v0.1 \
  --dry-run
```

The current template will correctly fail this default command because it does not yet contain enough approved documents to populate every split. To inspect its current decisions as a diagnostic only:

```bash
python3 src/build_pilot_corpus.py \
  --manifest corpus/pilot_sources.jsonl \
  --build-id pilot-v0.1 \
  --dry-run \
  --allow-incomplete-splits
```

After adding enough approved sources, create the immutable corpus build:

```bash
python3 src/build_pilot_corpus.py \
  --manifest corpus/pilot_sources.jsonl \
  --build-id pilot-v0.1
```

To replace an existing build only after a reviewed manifest change:

```bash
python3 src/build_pilot_corpus.py \
  --manifest corpus/pilot_sources.jsonl \
  --build-id pilot-v0.1 \
  --force
```

## Build outputs

| Output file | Contents |
|---|---|
| `corpus.jsonl` | All approved, normalized documents with retained lineage metadata. |
| `train.jsonl` | Source-level training partition. |
| `validation.jsonl` | Source-level held-out validation partition. |
| `test.jsonl` | Source-level final test partition. |
| `accepted_sources.jsonl` | Resolved approval records, observed hashes, and assigned splits. |
| `excluded_sources.jsonl` | Sources excluded by the approval gate or exact duplicate check. |
| `corpus_build_manifest.json` | Build ID, script version, source-manifest hash, counts, readiness, and full decision trace. |

The build manifest is the object that should be referenced by later tokenizer, training, evaluation, and model-card artifacts. A model run should never refer only to “the Aletheia corpus”; it should name an exact build ID and build-manifest hash.

## Pilot acceptance threshold

Do not train the 125M pilot merely because there is at least one document in each split. Before training, require a recorded review that confirms the target domain mix is reasonably balanced, all source records have a clear use basis, all first-party materials have an explicit training-use decision, no quarantined content leaked into the build, and the held-out evaluation split contains prompts for epistemic separation, record-versus-memory, technical accuracy, and emotionally careful conversation.

