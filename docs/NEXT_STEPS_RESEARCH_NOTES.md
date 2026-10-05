# Aletheia Next-Steps Research Notes

## Project-state finding

Aletheia’s current corpus build has two approved first-party documents, approximately 8,365 whitespace tokens, one training document, one validation document, and no test document. The repository correctly marks this diagnostic build as not training-ready. The project does, however, now have an approval-gated ingestion pipeline, a corpus validator, a train-only tokenizer utility, and a held-out 75-item epistemic evaluation suite.

## External findings

| Topic | Finding | Implication for Aletheia |
|---|---|---|
| Data provenance and curation | Desai et al. characterize pretraining data as a consequential archive: selection, documentation, privacy, and exclusion decisions shape downstream knowledge production. Their comparison highlights source documentation, quality filtering, privacy handling, and contamination controls as explicit dataset-design choices. [1] | Build the governed corpus before increasing model scale. Preserve source rights, provenance, sensitivity, and explicit inclusion decisions; do not treat text collection as a neutral bulk-download exercise. |
| Benchmark contamination | Xu et al. define benchmark contamination as exposure of evaluation material during training, which can inflate or distort measured performance. The survey describes matching-based and comparison-based detection and mitigation through new or refactored evaluation data. [2] | Preserve Aletheia’s 75-prompt suite as held-out; do not use it in pretraining, tokenizer training, or instruction tuning. Run it before and after material model changes. |
| Data–model trade-off | Hoffmann et al. found that, under a fixed compute budget, model size and training-token count should scale together; their evidence cautions against scaling parameters while holding the amount of training data effectively constant. [3] | Do not start a larger Aletheia model from the current tiny corpus. First obtain enough rights-cleared, balanced, held-out-evaluation-safe data to support a meaningful fresh tokenizer and pilot run. |

## Priority conclusion

The research reinforces two prerequisites: a **balanced, auditable corpus build** and a **baseline evaluation protocol that is protected from contamination**. More code, a larger model, retrieval, or prompt complexity would be lower-leverage at this stage because they would rest on inadequate data and lack a credible way to measure whether they improved the intended behavior.

## References

[1] Desai et al., “An archival perspective on pretraining data,” *Patterns* (2024). https://pmc.ncbi.nlm.nih.gov/articles/PMC11026960/

[2] Xu et al., “Benchmark Data Contamination of Large Language Models: A Survey” (2024). https://arxiv.org/html/2406.04244v1

[3] Hoffmann et al., “Training Compute-Optimal Large Language Models” (2022). https://arxiv.org/abs/2203.15556
