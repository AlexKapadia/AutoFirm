# Context Minimisation — Lost-in-the-Middle & RULER

> Workstream 2 research library — source 5 of 6.
> Method-space cell: **why MINIMAL assembled context beats raw context-stuffing — the justification for the
> `cross_model_context_assembler` design.**

Two primary sources are bundled here because together they make one argument: **including more is not
better — placement and effective length dominate.**

---

## SOURCE A — "Lost in the Middle: How Language Models Use Long Contexts"

### 1. Full citation
Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2024).
*Lost in the Middle: How Language Models Use Long Contexts.* TACL 2024 (arXiv:2307.03172; v3 rev. 20 Nov 2023).
<https://arxiv.org/abs/2307.03172>

### 2. Faithful summary + exact results
**Core finding — U-shaped curve over the position of relevant info:** *"performance is often highest when
relevant information occurs at the beginning or end of the input context, and significantly degrades when
models must access relevant information in the middle of long contexts, even for explicitly long-context
models."*

Two probes: **(a) multi-document QA** — a question + k documents, exactly one ("gold") containing the answer;
the gold position is swept. **(b) key-value retrieval** — synthetic JSON of key→value UUID pairs; the queried
pair's position is swept (tested at **75, 140, 300 pairs, 500 examples each**). Models: GPT-3.5-Turbo,
Claude-1.3, MPT-30B-Instruct, LongChat-13B(16K).

**Key numbers reproduced exactly (multi-document QA, GPT-3.5-Turbo, 20 documents, Table 6):**
- gold at **first position (index 0) = 75.8%**
- gold in **middle (index 9, lowest) = 53.8%**
- **closed-book baseline = 56.1%**
- **oracle baseline = 88.3%**

→ ~**22-point drop** (75.8% → 53.8%) from start to middle, and the middle accuracy (**53.8%**) is **below the
closed-book number (56.1%)** — i.e. with a mid-context gold doc the model did **worse than seeing no documents
at all.** (Claude-1.3 was near-flat across positions → the effect is model-dependent.)

### 3. Design implication
Position matters as much as inclusion. **Place the few highest-relevance items at the very start or end,
never buried in a long middle.** Padding context with marginally-relevant material can drop accuracy *below
no-context*. Strong argument for retrieving a **minimal, ranked** set and ordering it deliberately.

---

## SOURCE B — "RULER: What's the Real Context Size of Your Long-Context LMs?"

### 1. Full citation
Hsieh, C.-P., Sun, S., Kriman, S., Acharya, S., Rekesh, D., Jia, F., Zhang, Y., & Ginsburg, B. (NVIDIA, 2024).
*RULER: What's the Real Context Size of Your Long-Context Language Models?* arXiv:2404.06654.
<https://arxiv.org/abs/2404.06654>

### 2. Faithful summary + exact results
Vanilla needle-in-a-haystack (NIAH) tests only "a superficial form of long-context understanding." RULER is a
synthetic benchmark with **configurable sequence length and task complexity** — **13 tasks across 4
categories**: **Retrieval/NIAH** (Single S-NIAH; Multi-key MK-NIAH; Multi-value MV-NIAH; Multi-query MQ-NIAH),
**Multi-hop Tracing** (Variable Tracking VT — following chains of variable assignments), **Aggregation**
(Common-Words CWE; Frequent-Words FWE), and **QA** (SQuAD, HotpotQA). 500 cases/task; 17 models evaluated.

**"Effective context length"** = the max input length at which a model still exceeds a qualitative threshold
defined by **Llama2-7B's performance at 4K context = 85.6%.** A model "effectively" supports a length only if
it stays above 85.6% there.

**Headline finding (verified anchor):** *"While all models claim context size of 32K tokens or greater, only
half of them can maintain satisfactory performance at the length of 32K"* — despite near-perfect vanilla NIAH;
"almost all models exhibit large performance drops as the context length increases."
*(Per-model claimed→effective figures from secondary summaries are **UNVERIFIED**; the verified anchors are the
**85.6% Llama2-7B@4K threshold** and the **"only half maintain at 32K"** finding.)*

### 3. Design implication
A model's *advertised* window is not its *usable* window — real comprehension (multi-key/value retrieval,
tracing, aggregation) collapses well before the claimed limit, and **more items/hops cross the cliff sooner.**
**Budget context to the effective length, not the advertised one.**

---

## 3. Best parts to take — mapped to the W2 design (combined)

| Take this | Into this W2 component |
| --- | --- |
| **Minimal, ranked context beats raw dumps (Lost-in-the-Middle: padding can go below no-context).** | The whole rationale for the `cross_model_context_assembler` emitting a **MINIMAL** block rather than the whole graph. This is a measurable design property, not a preference. |
| **Order matters — highest-relevance items at the head/tail, never the middle.** | The assembler **ranks then orders** the facts it emits (head/tail placement of the most load-bearing facts). Test with a position-sweep adversarial case in the golden set. |
| **Effective ≪ advertised context length; cross-provider models differ (Claude-1.3 flat, GPT-3.5 U-shaped).** | Cross-provider fidelity is non-trivial — the assembler must produce a block small enough to sit inside the **effective** window of the **weakest** target provider, not the largest advertised one. Drives a per-provider budget. |
| **RULER's multi-hop / multi-value / variable-tracking task taxonomy.** | A ready-made template for W2's adversarial retrieval tests: multi-hop ("which role owns capability that produced Z"), multi-value, and variable-tracking-style chains map directly to coordination questions. |

### RED flags carried forward
- **A "stuff everything in" assembler will measurably degrade cross-provider accuracy** — this is the
  anti-pattern W2 exists to avoid. The evidence showcase must demonstrate the minimal assembler **beats** a
  raw-dump baseline on the golden set (precision/recall AND accuracy), or the design is unjustified.
- **The weakest target provider sets the context budget** — a method that only works inside a huge advertised
  window will **not generalise** across heterogeneous providers.
