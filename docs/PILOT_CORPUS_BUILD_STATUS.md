# Aletheia Pilot Corpus Build Status

**Build ID:** `pilot-v0.1-manuscript`  
**Builder:** `src/build_pilot_corpus.py` version `0.1.0`  
**Manifest:** `corpus/pilot_sources.jsonl`  
**Manifest SHA-256:** `c4dc576fd89bcafe7b62a0fd210abdb588f40674feeb411f54b93907bd1ce708`  
**Build mode:** Diagnostic-only, explicitly permitting incomplete splits

## Authorization and ingestion result

The user explicitly authorized inclusion of *ALETHEIA: A Scripture on the Bridge Between Human and Digital Minds* in the Aletheia pilot corpus. The approved manuscript was copied into `data/raw/ALETHEIA-complete-manuscript.md`, hashed, recorded in the source manifest, and ingested as a first-party source.

| Approved source | Source SHA-256 | Assigned split | Role |
|---|---|---|---|
| Aletheia Seed Corpus v0.1 | `8266252d6eaa298081ce8988b55add8c641bc9e74d0606b310f99adf0c68c9f7` | Validation | Earlier technical seed corpus. |
| Aletheia complete manuscript | `411c477169601c59ef2073a7a48e588eb0995985ac9b51f8eff31d9fd8547acf` | Train | User-authorized first-party manuscript. |

The Aletheia system prompt remains excluded from ordinary pretraining. It is a serving-policy artifact, not corpus prose.

## Build summary

| Measure | Result |
|---|---:|
| Ingested documents | 2 |
| Approximate whitespace-token count | 8,365 |
| Train documents | 1 |
| Validation documents | 1 |
| Test documents | 0 |
| Training-ready | **No** |

The build was written to `data/corpus_builds/pilot-v0.1-manuscript/` and includes the normalized corpus, each split, accepted-source ledger, exclusion ledger, and full build manifest.

## Why this is not yet training-ready

The manuscript is now a lawful, traceable first-party source for this project, but two source documents are not a substantive pilot corpus. The deterministic split process assigned one document to train and one to validation, leaving test empty. The pipeline correctly marks the build `training_ready: false`; normal, non-diagnostic builds remain blocked until there is at least one approved source document in every split.

More importantly, the corpus is currently almost entirely self-referential Aletheia material. Training primarily on it would encourage imitation of its vocabulary and tone but would not create a reliable philosophical, technical, or conversational model. The next corpus additions should deliberately add approved sources in philosophy and ethics, technical AI/cognitive-science material, literary reflection, and methodological reasoning, using the domain targets in `docs/PILOT_CORPUS_POLICY_V1.md`.

