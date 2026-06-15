# BEST-PARTS — APQC PCF Cross-Industry

## ADOPT (this is the single most load-bearing source for L1.B12.1)

1. **Adopt the PCF's level-split as AutoFirm's invariant/variant boundary.** This is the direct
   answer to "what makes a playbook general vs industry-specific": the **upper levels are the
   invariant** (Category -> Process Group -> Process are stable across all industries) and the
   **lower levels are the variant** (Activity -> Task "often vary among industries and
   organizations"). AutoFirm should structure every business playbook the same way: a fixed,
   cross-industry **process spine** with industry-parameterized **activity/task overrides**. This
   gives a principled, empirically-grounded definition of the invariant set rather than a guessed one.

2. **Adopt the 13 Categories as AutoFirm's canonical top-level function map (the invariant spine).**
   They already separate operating processes (1.0-6.0) from management/support (7.0-13.0) - the same
   primary/support split as Porter's value chain (B2.1) - and they are validated across "any
   industry." Use them as the master list every per-function playbook (B5-B11) plugs into, so the
   playbook set is provably complete and industry-agnostic at the top.

3. **Adopt stable element IDs as the join key.** The PCF's stable process-element identification
   numbers persist "even when process element names and definitions change across industries" -
   adopt this pattern: AutoFirm playbook steps carry stable IDs so an industry override re-binds the
   *content* of a step without breaking references, benchmarks, or audit lineage.

4. **Adopt the cross-industry + industry-specific layering pattern wholesale.** APQC ships one
   cross-industry PCF plus industry-specific variants - exactly the architecture AutoFirm needs:
   one general playbook + NAICS-keyed override packs (ties to source 01/03 parameterization).

## REJECT
1. **REJECT the PCF as a control-flow/orchestration model.** It is explicitly "not a process map,
   flow chart, or swim lane diagram" (claim 5). Use it as the *taxonomy/spine*; AutoFirm's actual
   execution order/orchestration comes from elsewhere (A1/A2). Do not try to derive run-time DAGs
   from the PCF.
2. **REJECT importing all 5 levels as fixed.** The Activity/Task levels are the *variant* surface -
   importing them as invariant would overfit to APQC's example decompositions (DEPTH-RUBRIC §6).
   Take the top 3 levels as the spine; generate/override the bottom 2 per industry.

## Build implication (concrete)
- Contract: `PlaybookSpine` = the 13 categories x process-groups x processes (stable IDs), shared by
  ALL industries; `IndustryOverridePack(naics_prefix)` supplies activity/task content per industry.
- This operationalizes the B12 thesis: a playbook is "general" iff it is expressed as
  (invariant spine + parameterized overrides), and "industry-specific" content lives ONLY in the
  override layer. Directly drives the L2.B12 generalization-layer design.
- Test: the spine resolves identically for all 8 fixed-panel rows; only override packs differ -
  proving generality (CLAUDE.md §3.9), with overfit = any industry leaking content into the spine.
