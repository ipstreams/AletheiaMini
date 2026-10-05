# Aletheia Corpus Tooling: Test Results

**Corpus build tested:** `pilot-v0.1-manuscript`  
**Corpus state:** Diagnostic-only; not training-ready  
**Tools tested:** `src/validate_corpus.py` and `src/train_corpus_tokenizer.py`

## Validation utility

The validator compiled successfully and ran against the current manuscript corpus build. In explicit diagnostic mode, it completed with **zero hard integrity errors** and **three readiness warnings**.

| Check | Result | Evidence |
|---|---|---|
| Build files and JSONL parsing | Passed | Required build outputs were present and parseable. |
| Source lineage and provenance | Passed | Both emitted documents mapped to accepted, approved sources. |
| Hash and split consistency | Passed | No duplicate document IDs, cross-split overlap, or normalized-content collision was reported. |
| Corpus readiness | Warning | The test split is empty. |
| Source diversity | Warning | The corpus has 2 unique sources; the default threshold is 3. |
| Corpus size | Warning | The corpus has approximately 8,365 whitespace tokens; the default threshold is 100,000. |

The normal validator mode turns these readiness findings into errors. The `--allow-unready-corpus` switch is required to downgrade them to diagnostic warnings. This prevents an incomplete corpus from being accidentally treated as ready for tokenizer training or pretraining.

## Tokenizer utility

A diagnostic Byte-Level BPE tokenizer was trained from the training partition only. The command used an intentionally small 300-token vocabulary and `--allow-unready-corpus`; it is a software test artifact, not the tokenizer for the future pilot model.

| Measure | Result |
|---|---:|
| Tokenizer ID | `pilot-v0.1-manuscript-bpe-300-diagnostic` |
| Requested / actual vocabulary | 300 / 300 |
| Training partition | Train only: one manuscript document |
| Training characters | 41,781 |
| Training tokenizer tokens | 29,443 |
| Training unknown-token rate | 0.0% |
| Validation tokenizer tokens | 6,052 |
| Validation unknown-token rate | 0.0% |
| Test documents | 0 |

The tokenizer manifest records the corpus-build ID, source hashes, train/validation/test file hashes, BPE configuration, special-token list, timestamp, and cross-split tokenization statistics. This establishes a reproducible tokenizer lineage.

## Readiness gate test

Tokenizer training was also run without `--allow-unready-corpus`. It correctly failed before creating an output tokenizer, stating that corpus validation must be resolved first. This confirms that the normal operation path cannot silently tokenize an incomplete corpus.

## Interpretation

The automation works as designed. It is ready to validate and tokenize expanded approved sources. The current BPE artifact must not be connected to Aletheia Tiny’s existing byte-level checkpoint, and it must not be treated as a pilot-model tokenizer. A production pilot tokenizer should be trained only after the corpus contains a meaningful, balanced train/validation/test split and has passed normal validation without the diagnostic override.

