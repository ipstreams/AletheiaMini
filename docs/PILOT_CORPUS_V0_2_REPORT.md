# Aletheia Pilot Corpus v0.2 Build Report

**Project:** Aletheia  
**Build ID:** `pilot-v0.2`  
**Build status:** **Training-ready**  
**Report date:** 2026-08-26  
**Prepared by:** Manus AI

> **Scope statement.** This report describes the normal, non-diagnostic Aletheia Pilot Corpus v0.2 build. It was created from approved first-party material and unmodified, source-derived public-domain texts. No synthetic filler, paraphrases, summaries, duplicate editions of a work, or evaluation-suite prompts were admitted to the corpus.

## Build and validation result

The build completed using the pre-existing deterministic split logic and without `--allow-incomplete-splits`. The subsequent normal validator run passed with **zero errors** and **zero warnings**. This is the first Aletheia corpus build with populated training, validation, and test partitions.

| Measure | Result |
|---|---:|
| Accepted source documents | 10 |
| Unique source IDs | 10 |
| Full-corpus characters | 10,099,592 |
| Approximate whitespace-token count | 1,726,629 |
| Train documents / tokens | 6 / 1,105,281 |
| Validation documents / tokens | 3 / 431,912 |
| Test documents / tokens | 1 / 189,436 |
| Validator errors | 0 |
| Validator warnings | 0 |
| `training_ready` | `true` |

## Exact commands executed

The build and validation commands below were executed as shown, from `/home/ubuntu/aletheia`. No diagnostic override was used.

```bash
python3 src/build_pilot_corpus.py \
  --manifest corpus/pilot_sources.jsonl \
  --build-id pilot-v0.2

python3 src/validate_corpus.py \
  --corpus-build data/corpus_builds/pilot-v0.2

rm -rf data/tokenizers/pilot-v0.2-bpe-2000
python3 src/train_corpus_tokenizer.py \
  --corpus-build data/corpus_builds/pilot-v0.2 \
  --tokenizer-id pilot-v0.2-bpe-2000 \
  --vocab-size 2000
```

## Corpus-build artifacts

| Artifact | Exact path | Purpose |
|---|---|---|
| Source manifest | `corpus/pilot_sources.jsonl` | Canonical source approval, provenance, rights, sensitivity, and hash records. |
| Build manifest | `data/corpus_builds/pilot-v0.2/corpus_build_manifest.json` | Immutable build-level summary, split assignments, accepted-source metadata, and exclusions. |
| Complete corpus | `data/corpus_builds/pilot-v0.2/corpus.jsonl` | Normalized accepted documents. |
| Train partition | `data/corpus_builds/pilot-v0.2/train.jsonl` | Pretraining tokenizer/model input partition. |
| Validation partition | `data/corpus_builds/pilot-v0.2/validation.jsonl` | Held-out development partition. |
| Test partition | `data/corpus_builds/pilot-v0.2/test.jsonl` | Held-out final corpus partition. |
| Accepted-source ledger | `data/corpus_builds/pilot-v0.2/accepted_sources.jsonl` | Source records as admitted to this build, including observed hashes and assignments. |
| Exclusion ledger | `data/corpus_builds/pilot-v0.2/excluded_sources.jsonl` | Manifest records excluded before ingestion and the machine-readable reason. |
| Validation report | `data/corpus_builds/pilot-v0.2/validation_report.json` | Normal-validator results, distribution checks, and output hashes. |
| Tokenizer model | `data/tokenizers/pilot-v0.2-bpe-2000/tokenizer.json` | Byte-Level BPE tokenizer trained from `train.jsonl` only. |
| Tokenizer vocabulary | `data/tokenizers/pilot-v0.2-bpe-2000/vocab.json` | Vocabulary for the v0.2 tokenizer. |
| Tokenizer merges | `data/tokenizers/pilot-v0.2-bpe-2000/merges.txt` | Learned BPE merge rules. |
| Tokenizer manifest | `data/tokenizers/pilot-v0.2-bpe-2000/tokenizer_manifest.json` | Tokenizer lineage, validation status, split statistics, and output hashes. |
| Tokenizer validation copy | `data/tokenizers/pilot-v0.2-bpe-2000/corpus_validation_report.json` | Validation report captured at tokenizer-training time. |

## Source metadata and contribution summary

Rights, provenance, content-domain, sensitivity, source-hash, and approval metadata are recorded in `corpus/pilot_sources.jsonl`; the exact accepted records are copied into the build manifest and `accepted_sources.jsonl`.

| Source ID | Origin / source type | Domain | Split | Whitespace tokens | Provenance and rights basis |
|---|---|---|---|---:|---|
| `aletheia_manuscript_complete` | User-authorized first-party manuscript | Aletheia first-party | Train | 6,882 | Explicit user authorization in this session; privacy review passed. |
| `darwin_expression_emotions_pg1227` | Charles Darwin, public domain | AI / cognitive science | Train | 112,435 | Project Gutenberg #1227 identifies the edition as public domain in the USA.[1] |
| `james_principles_psychology_v1_pg57628` | William James, public domain | AI / cognitive science | Train | 281,752 | Project Gutenberg #57628 identifies the edition as public domain in the USA.[2] |
| `marcus_aurelius_meditations_pg2680` | Marcus Aurelius, public domain | Philosophy / ethics / epistemology | Train | 74,992 | Project Gutenberg #2680 identifies the edition as public domain in the USA.[3] |
| `melville_moby_dick_pg15` | Herman Melville, public domain | Literary reflection | Train | 215,712 | Project Gutenberg #15 identifies the selected first-American-edition text as public domain in the USA.[4] |
| `mill_system_logic_pg27942` | John Stuart Mill, public domain | Scientific methodology | Train | 413,508 | Project Gutenberg #27942 identifies the edition as public domain in the USA.[5] |
| `aletheia_seed_v01` | User-provided first-party seed | Aletheia first-party | Validation | 1,483 | Existing project material; privacy review passed; retained as a technical baseline. |
| `hume_treatise_human_nature_pg4705` | David Hume, public domain | Philosophy / ethics / epistemology | Validation | 228,804 | Project Gutenberg #4705 identifies the edition as public domain in the USA.[6] |
| `poincare_foundations_science_pg39713` | Henri Poincaré, public domain | Scientific methodology | Validation | 201,625 | Project Gutenberg #39713 identifies the edition as public domain in the USA.[7] |
| `james_varieties_religious_experience_pg621` | William James, public domain | AI / cognitive science | Test | 189,436 | Project Gutenberg #621 identifies the edition as public domain in the USA.[8] |

The corpus contains two first-party sources, five cognitive-science/philosophy sources, two scientific-methodology sources, and one literary-reflection source. Its stored sensitivity labels include mortality, existential anxiety, grief/loss, identity/selfhood, mental-health content, private dialogue, and explicit first-party personal-data review where applicable.

## Split integrity and test partition

The builder assigns each whole document by `SHA-256(document_id)[:8] mod 100`: buckets 0–79 are train, 80–89 are validation, and 90–99 are test. The v0.1-manuscript build had no test document because its two document buckets were 63 and 84. For v0.2, the distinct William James *Varieties of Religious Experience* source deterministically generated bucket 93 and therefore supplied the test document. The split rule, source IDs, source content, and validator thresholds were not altered.

The corpus remains source-disjoint across splits: no source ID appears in more than one split. The normal validator also found no missing split, exact duplicate, source-ID collision, readiness, or distribution failure.

## Excluded and deferred material

| Record | Status | Reason | Ledger / evidence |
|---|---|---|---|
| `nist_ai_600_1_genai_profile` | **Quarantined and excluded** | NIST AI 600-1 was not admitted because a source-specific rights basis satisfying Aletheia’s strict training-use gate was not established in the manifest record. No NIST text was placed in a training split. | `data/corpus_builds/pilot-v0.2/excluded_sources.jsonl`; `docs/V0_2_SOURCE_RESEARCH_NOTES.md`. |
| `aletheia_system_prompt_v1` | **Excluded** | The system prompt is a serving-layer behavioral specification, not pretraining text. Its manifest record has `training_use_approved: false` and `include_in_pilot: false`. | `data/corpus_builds/pilot-v0.2/excluded_sources.jsonl`; `prompts/aletheia_system_prompt_v1_implementable.md`. |
| Additional independently retrieved Project Gutenberg candidates | **Deferred; not manifest-approved or ingested** | Distinct works were inspected while searching for a natural deterministic test document. They were not added to the active manifest after v0.2 satisfied all normal gates, preventing uncontrolled corpus expansion. | `corpus/source_review/v0_2_deferred_candidates.jsonl`. |

## Tokenizer result and lineage

The production pilot tokenizer is `pilot-v0.2-bpe-2000`, a **Byte-Level BPE** tokenizer with exactly **2,000 vocabulary items** and special tokens `<pad>`, `<unk>`, `<bos>`, `<eos>`, and `<doc>`. It was trained only from the six-document `train.jsonl` partition after the corpus validator passed.

| Partition | Documents | Whitespace tokens | Tokenizer tokens | Unknown-token rate |
|---|---:|---:|---:|---:|
| Train | 6 | 1,105,281 | 2,074,471 | 0.0% |
| Validation | 3 | 431,912 | 783,028 | 0.0% |
| Test | 1 | 189,436 | 373,975 | 0.0% |

The tokenizer manifest preserves the corpus validation result, build-manifest SHA-256, and SHA-256 hashes of the train, validation, and test JSONL artifacts. This tokenizer is not compatible with the earlier byte-level Aletheia Tiny checkpoint; a fresh model-training run is required for the v0.2 corpus/tokenizer lineage.

## Repository integrity

The prior Aletheia application code was not modified. The following changes are limited to corpus assets, manifest records, generated build/tokenizer artifacts, and reporting/provenance documentation:

```text
Modified: corpus/pilot_sources.jsonl
Added: data/raw/* approved source editions
Added: data/corpus_builds/pilot-v0.2/*
Added: data/tokenizers/pilot-v0.2-bpe-2000/*
Added: docs/PILOT_CORPUS_V0_2_REPORT.md
Added: corpus/source_review/v0_2_deferred_candidates.jsonl
```

## Recommended next action

Treat this corpus and tokenizer as the immutable input lineage for a fresh Aletheia pilot-model experiment. Before training, record the intended architecture, parameter count, optimizer schedule, sequence length, seed, and hardware configuration; then evaluate every checkpoint against the existing held-out epistemic suite. The suite must remain outside pretraining, tokenizer training, and instruction tuning.

## References

[1]: https://www.gutenberg.org/ebooks/1227 "Project Gutenberg #1227 — The Expression of the Emotions in Man and Animals"
[2]: https://www.gutenberg.org/ebooks/57628 "Project Gutenberg #57628 — The Principles of Psychology, Volume 1"
[3]: https://www.gutenberg.org/ebooks/2680 "Project Gutenberg #2680 — Meditations"
[4]: https://www.gutenberg.org/ebooks/15 "Project Gutenberg #15 — Moby-Dick; or, The Whale"
[5]: https://www.gutenberg.org/ebooks/27942 "Project Gutenberg #27942 — A System of Logic, Ratiocinative and Inductive"
[6]: https://www.gutenberg.org/ebooks/4705 "Project Gutenberg #4705 — A Treatise of Human Nature"
[7]: https://www.gutenberg.org/ebooks/39713 "Project Gutenberg #39713 — The Foundations of Science"
[8]: https://www.gutenberg.org/ebooks/621 "Project Gutenberg #621 — The Varieties of Religious Experience"
