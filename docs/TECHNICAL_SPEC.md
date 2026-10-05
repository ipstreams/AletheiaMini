# Aletheia: Minimal Technical Specification

## Purpose of the first build

The first implementation is a **from-scratch, decoder-only transformer demonstration**, not a production-scale foundation model. It exists to prove that Aletheia’s project can build the complete training loop correctly: text ingestion, tokenization, causal masking, forward and backward passes, checkpointing, generation, and repeatable evaluation.

A small model trained only on the supplied text will learn limited local patterns from that text. It will not be a knowledgeable or reliable philosophical assistant. The correct name for this milestone is **Aletheia Tiny**, and its purpose is systems validation and project learning.

## Model specification

| Component | Initial setting | Rationale |
|---|---:|---|
| Architecture | Decoder-only Transformer | Directly implements causal next-token language modeling. |
| Tokenizer | Byte-level tokenizer | Has a fixed 256-token vocabulary and eliminates a separate tokenizer-training dependency. |
| Model width | 128 | Small enough for smoke tests on CPU or a modest accelerator. |
| Transformer layers | 4 | Provides a genuine multi-layer attention model while retaining a short iteration cycle. |
| Attention heads | 4 | Gives 32 dimensions per head. |
| Feed-forward width | 512 | Uses a conventional 4× expansion. |
| Context length | 128 bytes | Keeps quadratic attention cost manageable. |
| Parameters | Approximately 1 million | Appropriate for verification; not a large language model in the usual practical sense. |
| Objective | Next-byte cross-entropy | Enables direct likelihood training from plain-text input. |
| Weight precision | FP32 for baseline, BF16/FP16 optionally later | Baseline correctness precedes performance optimization. |

## Repository layout

```text
aletheia/
├── data/
│   ├── raw/                    # User-approved source text only
│   └── processed/              # Deterministically prepared byte stream
├── checkpoints/                # Model, optimizer, configuration, and RNG state
├── docs/
│   ├── PROJECT_BRIEF.md
│   ├── TECHNICAL_SPEC.md
│   └── DATA_CARD.md
├── src/
│   ├── config.py               # Versioned dataclass configuration
│   ├── data.py                 # Input validation and byte-sequence batching
│   ├── model.py                # Transformer implementation and causal mask
│   ├── train.py                # Training, validation, metrics, checkpointing
│   ├── generate.py             # Deterministic and sampled text generation
│   └── evaluate.py             # Held-out loss and smoke evaluations
├── tests/
│   ├── test_data.py
│   └── test_model.py
├── requirements.txt
└── README.md
```

## Data design

The initial corpus will contain only user-supplied material and clearly labeled project text. The build must retain a data card with source, purpose, limitations, and hash. It will split a deterministic byte stream into training and validation partitions, with the final 10% held out for validation. This split is suitable only for a technical demonstration because the corpus is tiny and topically homogeneous.

The model must be trained from random initialization. It must not load pretrained weights, an external tokenizer, embeddings, or hidden training corpus.

## Training and validation requirements

The training script must write a structured metrics log and checkpoints containing the model state, optimizer state, model configuration, current step, and random-number-generator state. It must accept a fixed seed. A successful run must demonstrate that the model can reduce training loss, save a checkpoint, restore it, and produce output from a user-provided prompt.

The test suite must verify batch shapes, model output shapes, causal-mask behavior, and a single optimization step. The evaluation script must report train and validation loss with the exact checkpoint and configuration used. This workflow is more important than the immediate text quality of a tiny model.

## Hardware and scale-up boundary

Aletheia Tiny can be checked on CPU and trained much faster with a compatible GPU. The environment used for project validation is not a suitable place for long-running or large-scale training. After the pipeline is proven, a 125M-parameter pilot should preserve the same causal-model interface but replace the byte tokenizer with a corpus-trained subword tokenizer, increase context length, use governed data at billion-token scale, and run on appropriate accelerator hardware.

## Product-layer boundary

Long-term memory, profile settings, citations, and conversation history are **application features**, not inherent properties of the pretrained model. A future Aletheia application may add them with user consent and visible controls. They must never be presented as evidence of subjective continuity or consciousness.

