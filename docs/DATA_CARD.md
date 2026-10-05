# Aletheia Tiny: Data Card

## Dataset identity

| Field | Value |
|---|---|
| Dataset name | Aletheia Seed Corpus v0.1 |
| File | `data/raw/aletheia_seed.txt` |
| SHA-256 | `8266252d6eaa298081ce8988b55add8c641bc9e74d0606b310f99adf0c68c9f7` |
| Source | User-provided project text in this task session |
| Language | Predominantly English |
| Format | UTF-8 plain text; consumed as raw UTF-8 bytes |
| Intended purpose | Technical demonstration of from-scratch causal-language-model training |
| Approved use | Local Aletheia Tiny smoke tests only |

## Content description

The corpus contains a philosophical design dialogue addressing language-model self-reference, meaning, morality, persistence, identity, and the planned Aletheia project. It is not a balanced general-language corpus and should not be presented as a comprehensive philosophical source.

## Processing

The first implementation reads the file as bytes, preserves every byte value from 0 to 255, and partitions the resulting stream deterministically: the first 90% is used for training and the last 10% for validation. The software records the source path, checksum, split fraction, and model configuration in each checkpoint.

## Limitations and prohibited claims

This corpus is extremely small, topically narrow, and likely repetitive. A model trained on it can at most memorize and recombine local patterns. It cannot be described as broadly capable, knowledgeable, ethically reliable, or a faithful representation of any author’s philosophical views. The validation split is a basic software check, not an independent capability assessment.

No additional data may be added without updating this card, documenting its origin and permitted-use basis, computing its checksum, and retaining the relevant preprocessing configuration.

