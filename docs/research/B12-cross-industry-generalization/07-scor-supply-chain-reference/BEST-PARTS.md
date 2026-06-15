# BEST-PARTS — SCOR (Supply Chain Operations Reference)

## ADOPT
1. **Adopt SCOR as proof-by-example that a TINY universal spine generalizes across all industries.**
   SCOR reduces ALL supply chains to ~6 top processes (Plan/Source/Make/Deliver/Return/Enable) and
   configures beneath. This validates AutoFirm's bet: the invariant spine can be small and still
   cover every industry, with all real variation pushed into the configuration/override layer
   (corroborates APQC source 04 and C-EPC source 05 in the operations domain).

2. **Adopt SCOR's four-component anatomy as the template for each AutoFirm playbook.** Every
   playbook should ship not just process steps but also: (a) attached **metrics/benchmarks**,
   (b) **best practices**, and (c) a **configuration** for the specific instance. The metrics piece
   is the key add - it makes each playbook self-evaluating, feeding the evidence/ showcase
   (CLAUDE.md §3.10) and giving the B12 generalization test a quantitative "is the output sensible?"
   signal per industry.

3. **Adopt the metrics-attached-to-process pattern for B11/B4.3.** SCOR pairs each process with
   standard KPIs; AutoFirm's operations playbook should likewise carry industry-parameterized KPI
   targets (e.g. delivery reliability, cycle time) so generality is measured, not asserted.

## REJECT
1. **REJECT SCOR's domain scope as the whole model.** SCOR covers ONLY supply-chain/operations - it
   is one PCF category (deliver/operate), not the whole company. Use it to design the operations
   playbook (B11) and as architectural proof-of-concept for the spine pattern, NOT as the master
   spine (that role is APQC's 13 categories, source 04).
2. **REJECT static SCOR levels.** SCOR DS is evolving (orchestration/sustainability added). Mirror
   this: AutoFirm spines/metrics must be versioned, not frozen.

## Build implication (concrete)
- The operations/delivery branch of `PlaybookSpine` adopts SCOR DS top processes as its sub-spine,
  with NAICS-keyed override packs supplying industry-specific activities/KPIs beneath.
- Each playbook step gains an attached `metrics: KPI[]` field (SCOR pattern) with
  industry-parameterized targets -> directly feeds the B12 panel test's "sensible result" check and
  the evidence/ charts (accuracy/throughput per industry).
- Test: for every fixed-panel row, the operations sub-spine resolves with a non-empty, industry-
  appropriate KPI set (physical industries get throughput/lead-time KPIs; digital get uptime/latency)
  - demonstrating the metrics layer generalizes, not just the steps.
