# BEST-PARTS — AgentDojo

## ADOPT
1. **Use AgentDojo (or its design) as AutoFirm's standing injection-defense eval harness.** It is the peer-reviewed, extensible, adaptive-attack environment AutoFirm needs to *prove* (not assert) its A7 defenses have teeth (CLAUDE.md §3.6/§3.10). *Build:* a CI/evidence job runs AutoFirm's tool-using agents through AgentDojo-style tasks + injection points and reports secure-task-completion % and attack-success-rate.
2. **Adopt its threat realism:** injection points embedded in *retrievable data* across realistic domains (workspace, banking, travel) — exactly AutoFirm's operating context (reading filings, sending comms, calling APIs). *Build:* AutoFirm's red-team test fixtures mirror these domains with synthetic data (CLAUDE.md §3.6 synthetic fixtures).
3. **Adopt "adaptive attacks, not a static leaderboard."** A defense must survive *adaptive* attackers, not one fixed corpus — drives AutoFirm's red-team tests to be adversarial and evolving (CLAUDE.md §3.7 iterate-to-perfection: if attacks stop landing, make them harder).

## REJECT / DEFER
- **Do not overfit to AgentDojo's four domains** (CLAUDE.md §3.9 generality) — it is a *sample* of the surface; AutoFirm must also test its own real tool set. Use AgentDojo as a calibrated baseline, then extend.

## Concrete build implications
- Provides the **measurable security KPI** for the `evidence/` showcase: secure-task-completion % and attack-success-rate before/after defenses (mirrors source 08's ASR 78%->9.1%).
- Gives AutoFirm an **external, peer-reviewed yardstick** so its injection-defense claims are regulator-defensible, not self-graded.
