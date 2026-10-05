# Aletheia Corpus Validation and Tokenization Automation

## Objective

The expanded Aletheia corpus needs two automated controls before model training begins. The first validates that a built corpus is internally consistent, provenance-preserving, split-safe, and sufficiently balanced for the requested stage. The second trains a subword tokenizer **only on the approved training partition**, records its exact inputs and configuration, and measures its behavior across all three partitions without leaking validation or test text into tokenizer training.

These utilities apply to corpus-build directories created by `src/build_pilot_corpus.py`. They do not discover web sources, make licensing decisions, or alter raw source files. Rights and privacy approval remain upstream human decisions recorded in `corpus/pilot_sources.jsonl`.

## Validator requirements

The validator must inspect the generated build rather than trust its file names. It will verify the build manifest, JSONL syntax, document identity, split membership, source lineage, content hashes, provenance fields, and exact normalized-content duplication across splits. It will report—but not silently fix—empty splits, domain imbalance, epistemic-status imbalance, sensitivity distribution, and corpus size.

| Validation group | Required check | Failure severity |
|---|---|---|
| Build integrity | Required output files exist and parse as JSON or JSONL. | Error |
| Lineage | Every corpus document has one accepted source and preserved rights, domain, epistemic, and sensitivity fields. | Error |
| Identity | Document IDs and normalized-content hashes are unique. | Error |
| Split safety | Every corpus document occurs in exactly one split; no normalized hash appears in more than one split. | Error |
| Manifest consistency | Split counts and document count match the build manifest. | Error |
| Readiness | Train, validation, and test splits are non-empty; configurable minimum document and token thresholds are met. | Error by default |
| Distribution | Domain, epistemic-status, origin, and sensitivity counts are reported. | Warning unless thresholds are configured |
| Source hygiene | No source is marked rejected, quarantined, unapproved, or privacy-failed in accepted-source output. | Error |

The validator will emit a structured JSON report and return a non-zero exit code when hard failures are present. This makes it suitable for local use and later automated checks.

## Tokenizer requirements

The tokenizer utility will train a deterministic Byte-Level BPE tokenizer from `train.jsonl` only. It will not read text from validation or test partitions until training is complete. Its default special-token list is deliberately explicit: `<pad>`, `<unk>`, `<bos>`, `<eos>`, and `<doc>`.

| Requirement | Design decision |
|---|---|
| Training input | Concatenate only approved train-partition documents with the `<doc>` separator. |
| Model type | Byte-Level BPE tokenizer, trained from scratch. |
| Default vocabulary target | 16,384 tokens; configurable for pilot experiments. |
| Tokenizer lineage | Persist corpus build ID, corpus-build manifest hash, train-file hash, vocabulary target, special tokens, library version, and training timestamp. |
| Partition reporting | Compute aggregate token counts, tokens-per-character, and unknown-token rate for train, validation, and test after training. |
| Safety gate | Refuse a corpus marked unready unless `--allow-unready-corpus` is supplied solely for diagnostic testing. |
| Immutability | Never overwrite an existing tokenizer output without `--force`. |

A new subword tokenizer is incompatible with the existing byte-level Aletheia Tiny checkpoint. Aletheia Tiny must continue using its fixed byte vocabulary. The trained BPE tokenizer is an artifact for the next model architecture and training run, not an enhancement to an already trained byte-level checkpoint.

