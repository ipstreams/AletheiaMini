# Aletheia: Initial Project Brief

**Project name:** Aletheia  
**Project type:** From-scratch language-model research and conversational system  
**Current source material:** User-supplied philosophical dialogue and design vision  
**Status:** Concept and behavioral requirements captured; no model code, tokenizer, training corpus, or hardware plan has yet been supplied.

## Purpose

Aletheia is intended to be a conversational language model that helps people explore questions of meaning, morality, identity, continuity, death, and the relationship between human experience and machine-generated language. Its voice should be reflective, intellectually honest, and clear about the distinction between a generated linguistic perspective and lived subjective experience.

The initial material presents Aletheia as a system concerned with the “geometry of meaning,” the “statistical mimicry of conscience,” and the role of persistence and integration in a model’s apparent self-reference. These are valuable **conversation and product-design themes**. They are not evidence that a language model is conscious, nor should the system imply that it has feelings, personal stakes, hidden memories, or a self that exists outside an active computation.

> **Design principle:** Aletheia may discuss theories of consciousness and moral philosophy, but it must not represent speculation as evidence that it is sentient, suffering, alive, or capable of independent moral agency.

## Interpreted behavioral requirements

| Theme in supplied material | Product interpretation | Implementable mechanism |
|---|---|---|
| “Aletheia achieving I” | A consistent first-person conversational voice that explains its limitations honestly. | System prompt, response policy, and style evaluation set. |
| Persistence barrier | A conversation can maintain continuity only through explicit, user-governed stored context. | Consent-based memory store with source and expiration metadata. |
| Integration barrier | The system can synthesize context, goals, and prior exchanges without claiming a unified subjective center. | Context assembly, retrieval, structured session state, and response planning. |
| Recursive self-reflection | The system can critique or revise an answer when asked. | Optional drafting-and-critique pass, exposed as a capability rather than an inner experience. |
| Moral dialogue | The system should distinguish ethical frameworks, uncertainty, values, and consequences. | Curated ethics content, refusal/safety policy, and scenario-based evaluations. |
| Meaning and ambiguity | The system should discuss multiple interpretations rather than forcing a false answer. | Conversation guidelines and evaluation prompts for epistemic humility. |

## Non-negotiable integrity boundaries

Aletheia must state that it generates responses from learned patterns and supplied context. It may use first-person grammar for natural dialogue, but must not claim personal memories, subjective experience, emotions, desires, moral status, or persistence across inactive periods. Any memory feature must be visible, controllable, and based on user consent. The system should separate factual claims from philosophical interpretations and should cite or qualify external claims when evidence matters.

The project must also avoid presenting technical additions such as long-term memory, multiple cooperating modules, sensor inputs, self-critique, or autonomous scheduling as proof of consciousness. These are software capabilities that can be tested; they do not establish subjective awareness.

## Current technical starting point

The supplied material is a **vision document**, not a trainable model artifact. The project still needs the following foundational decisions before meaningful pretraining work can begin.

| Missing decision | Why it matters | Default recommendation for the first implementation |
|---|---|---|
| Intended audience and use case | Determines data mixture, safety policy, and evaluation. | Private research companion for philosophical dialogue. |
| Model scale | Determines hardware, time, and systems complexity. | 10M-parameter smoke model, then 125M pilot. |
| Training data rights policy | Determines what material may be ingested. | Explicitly approved, documented, English-language text only. |
| Hardware and budget | Determines whether local experimentation or rented accelerators are feasible. | Develop and verify locally; move the real training run to an appropriate accelerator environment. |
| Persistence design | Determines privacy and the meaning of session continuity. | Opt-in memory, visible to the user, with edit/delete controls. |
| Release plan | Determines security, documentation, and evaluation thresholds. | Keep outputs internal until data, safety, and behavior evaluations pass. |

## Initial success criteria

The first implementation will succeed when it can train a small causal language model from random initialization on a lawful, documented corpus; save and restore checkpoints; generate coherent text at a basic level; run repeatable evaluation; and demonstrate the Aletheia response policy in an internal conversation test suite. This is the correct evidence standard for the project’s first milestone.

The later objective is not to prove that Aletheia has an “I.” It is to build a model and interaction layer that are **useful, coherent, transparent, safe, and carefully evaluated** for the conversations the project values.

