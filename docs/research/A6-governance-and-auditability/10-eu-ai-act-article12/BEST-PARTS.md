# BEST-PARTS — EU AI Act Art. 12 for AutoFirm

## ADOPT
1. **Adopt "automatic, over-the-lifetime" logging as a hard, non-optional AutoFirm requirement.** Manual documentation does not satisfy Art. 12; AutoFirm's substrate MUST auto-emit audit events for the full lifecycle of every agent/run/client-system — from spawn to retirement. This is the legal force behind CLAUDE.md §5.6's append-only audit log. *Build implication:* logging is a platform default, not a per-project add-on (L2.A6).
2. **Adopt the three logged-event purposes (a/b/c) as the taxonomy of what MUST be auditable:** (a) risk-presenting situations + substantial modifications, (b) post-market monitoring data, (c) operational monitoring. AutoFirm's GTS/audit schema (source 07) includes event categories mapping to a/b/c so compliance is by-construction.
3. **Adopt the biometric minimum-log fields as a template for high-risk action logging generally:** time period, the data/source consulted, the input that triggered a match/decision, and the identity of the human/agent who verified — i.e. who/what/when/which-inputs. This maps onto PROV (Activity/Entity/Agent) + FHIR (recorded/agent.who) (sources 01/02).
4. **Adopt a ≥6-month retention floor (default longer)** as the audit-log retention policy; make retention + lawful deletion explicit (ties to ISO 42001 records control, source 12, and FHIR `entity.role=removal`, source 02).

## REJECT / DEFER
- **Reject treating Art. 12 as the *ceiling*.** It is a floor; AutoFirm targets institution-grade (CLAUDE.md §3.2), so tamper-evidence (sources 03/04/06) and closed-loop enforcement (07/08) exceed the bare legal minimum. Do not design *down* to six months / plain logs.
- **Defer the formal high-risk classification per client** to the L2.B10 legal playbook; A6 provides the logging capability regardless of classification (build it always; it is cheap insurance).

## Why (cited)
This is the binding regulatory anchor that makes A6 non-negotiable for real-world EU deployments — it converts "good audit hygiene" into a legal obligation and defines the minimum event taxonomy and retention AutoFirm must meet (CLAUDE.md §3.2 regulator-grade scrutiny).
