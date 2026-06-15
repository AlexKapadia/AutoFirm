# BEST-PARTS — Ma & Tsudik attacks/FssAgg for AutoFirm

## ADOPT
1. **Adopt the truncation attack and delayed-detection attack as explicit, named threats in the A6 threat model** (CLAUDE.md §5.6 maintained threat model). This is the key lesson: a naive hash chain (source 03) is NOT enough — an attacker who deletes the tail leaves a shorter, internally-consistent chain. AutoFirm's audit design MUST defend tail-truncation, not just mid-log tampering.
2. **Adopt forward-security (key evolution) for the audit-signing key.** The key that seals audit records evolves and old key material is destroyed, so compromising the live agent host cannot retroactively re-sign rewritten history. This is fail-closed against a compromised executor — directly relevant since AutoFirm runs autonomous agents that could be subverted (A7 threat models).
3. **Adopt anti-truncation by construction**, satisfied two complementary ways: (a) periodic externally-published commitments / consistency proofs (sources 04, 06) so an auditor knows the expected length and detects a short log; and (b) FssAgg-style aggregate sealing where AutoFirm controls the keys. Prefer (a) as primary (simpler, dependency-light, externally verifiable) with (b) as defence-in-depth.

## REJECT / DEFER
- **Reject FssAgg as the sole/primary mechanism.** Its aggregate-signature crypto is heavier and harder to externally verify than published commitments + consistency proofs (history tree, CT). **Adopt its threat insight and forward-security; reject it as the primary data structure.**
- **Defer the public-key vs MAC variant choice** to L2.A6 implementation (depends on whether external parties must verify without AutoFirm's secret).

## Why (cited)
Without this source, AutoFirm would ship a hash chain that *looks* tamper-evident but silently permits tail-truncation — exactly the false-confidence failure CLAUDE.md §3.6 warns against. It hardens the tamper-evidence claim and is the third independent primary corroborating it (with 03, 04, 06).
