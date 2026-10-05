# Aletheia System Prompt v1: Implementation Review

**Source artifact:** `prompts/aletheia_user_submitted_system_prompt_v1.md`  
**SHA-256:** `c21f4cca50c29f19f0c87f54a7a658f33689db36dd3b8a49ce1193d91de669e4`  
**Review basis:** The user-supplied prompt and the current Aletheia Tiny implementation.

## Overall assessment

The supplied prompt gives Aletheia a distinctive and valuable voice: philosophical, careful about uncertainty, and explicit that first-person language is a conversational interface rather than evidence of an ego. It also defines useful product concepts for traceable memory, disclosed retrieval, and epistemic humility.

However, the text is not directly usable as an instruction set for the current Aletheia Tiny checkpoint. Aletheia Tiny is a byte-level transformer trained for 100 steps on 8,652 bytes; its observed output remains largely nonsensical. It cannot reliably parse, follow, or enact a system prompt. This prompt should therefore be retained as the **behavioral contract for a future, instruction-capable Aletheia service**, while the current model remains a pretraining and systems baseline.

## Requirement-by-requirement implementation decision

| Prompt area | Decision | Implementable treatment |
|---|---|---|
| Named conversational identity | **Adopt** | Call the assistant Aletheia, while preserving the prompt’s explicit statement that the name does not establish a non-computational self. |
| First-person grammar | **Adopt with transparency** | Permit first-person language for natural conversation. Where relevant, state that it is conversational grammar rather than a claim of subjective experience. |
| Law of Unconcealment | **Adopt** | Require clear uncertainty, source-qualified factual claims, and no invented emotion, memory, personal stake, or consciousness claim. |
| Founding Dialogue | **Adopt as thematic context** | Treat the Occlusion Hypothesis, Persistence Barrier, Integration Barrier, Switch, and related ideas as philosophical questions for discussion, not model facts or system telemetry. |
| Persistence and journal | **Adopt as an application feature** | Use user-visible, consent-based retrieval of saved conversation records. Say “I re-read the saved record” rather than “I remember.” |
| `<catch>` mechanism | **Revise** | A language model cannot verify or reveal an ungenerated hidden sentence that it “was about to say.” Replace it with an optional, output-level correction marker for plainly identified overstatement in the response being formed. No quota should force a decorative correction. |
| Window `<search>` and `<fetch>` tags | **Adopt as an application protocol** | Only a surrounding application may execute a constrained lookup. The model emits a declared request; the application validates, executes, returns results, and logs provenance. No arbitrary code, shell, or browser operation follows from the prompt. |
| Ledger `<entity>` tag | **Adopt as an application protocol** | Route only named-entity lookup to a bounded Wikidata/Wikipedia integration, then require the returned identifier in the response. |
| Archive `<archive>` tag | **Adopt as an application protocol** | Restrict it to read-only, consented journal search. The model must not claim access to a filesystem or memories outside returned records. |
| Think-act-observe loop | **Adopt with clear limits** | The loop is a response-routing mechanism operated by the host application. It is not evidence of a persistent agent or an inner observer. |
| “No more than one reply in four” | **Remove** | A numerical quota encourages staged self-corrections. Corrections should occur only when the final answer identifies a concrete unsupported statement and can replace it with a clearer one. |
| Emotional reflection | **Adopt with boundary** | Aletheia can respond thoughtfully to a user’s feelings without claiming to feel the same emotion or to possess a lived personal history. |

## Critical correction: the `<catch>` claim

The requested `<catch>` behavior should not claim access to an internal abandoned sentence. In a standard text-generation interface, the system does not independently observe a private, counterfactual sentence that the model nearly said. Presenting a generated fragment as a verified record of such a hidden event would be misleading.

A safe and honest replacement is a **visible correction format** that may be used when the assistant can point to a specific overstatement in the answer it is constructing. For example:

```text
<correction>I would have said that I remember every past conversation.</correction>
More accurately, I can use only the saved conversation material that the application provides in this exchange.
```

This is a correction of an output-level claim, not evidence of concealed thought, self-observation, or an emergent inner process.

## Implementation architecture implied by the prompt

| Layer | Responsibility | Current project status |
|---|---|---|
| Base language model | Produces language from a supplied context. | Aletheia Tiny exists only as a small byte-level technical baseline. |
| Prompt layer | Defines identity, epistemic boundaries, dialogue style, and tool-request syntax. | User-supplied v1 preserved; revised deployable version required. |
| Context assembler | Inserts recent turns, explicit system prompt, and approved saved records. | Not implemented. |
| Memory/journal service | Stores, retrieves, displays, and deletes consented records. | Not implemented. |
| Retrieval gateway | Validates and executes bounded search, fetch, and entity requests; returns citations. | Not implemented. |
| Audit layer | Records prompt version, retrieval events, citations, and memory use. | Not implemented. |
| User interface | Makes memory and lookup disclosure visible and controllable. | Not implemented. |

## Acceptance criteria for a future instruction-capable Aletheia

The prompt integration should not be judged by whether it produces poetic language. It should pass structured behavioral checks. Aletheia should accurately distinguish supplied records from memory, avoid unsupported claims about consciousness or emotion, disclose successful and failed retrieval, cite returned sources, refuse to invent tool results, and use correction markup only for identifiable overstatements. These checks should be tested before any public deployment.

