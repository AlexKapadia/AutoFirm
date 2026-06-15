# BEST-PARTS — NIST SP 800-218 (SSDF)

## ADOPT
1. **SSDF as the secure-SDLC backbone for all client software.** Its four practice groups (PO/PS/PW/RV) map cleanly onto AutoFirm phases: PO -> Gate 0 bootstrap (security requirements, toolchain), PW -> Gate 2 build (threat model, secure design, SAST/DAST/fuzz, code review), PS -> release (provenance, SBOM, signed artifacts), RV -> post-ship (vuln response, root-cause). This gives a citable, government-grade definition of "institution-grade secure SDLC" (CLAUDE.md §3.2/§5.6).
2. **PW.7/PW.8 mandate both review and automated analysis** — directly grounds the requirement that AutoFirm runs SAST + DAST + fuzz *and* an independent (generator/evaluator-split) review on every client build.
3. **PS.3 provenance/SBOM** — ties client delivery to the A6 audit/provenance work: every release archived with provenance + SBOM. Supply-chain integrity by default.
4. **SP 800-218A (GenAI profile)** — directly relevant because AutoFirm *is* an AI system producing software; adopt its additional practices for AI-generated code (provenance of generated code, evaluation of training/model risks where applicable).

## REJECT
- Don't treat SSDF as a checkbox compliance artifact — it is outcome-focused; AutoFirm must implement the *outcomes* (fewer vulns, fast remediation), proven by the SAST/DAST/fuzz/mutation evidence, not just claim the practice IDs.

## Concrete artifact this drives
- A `secure-sdlc-manifest` per client product mapping each shipped control to an SSDF task ID (PO/PS/PW/RV), with the SBOM + provenance record — auditable, fail-closed, and regulator-defensible.
