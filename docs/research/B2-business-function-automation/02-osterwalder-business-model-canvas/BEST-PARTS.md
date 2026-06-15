# BEST-PARTS — Business Model Canvas → AutoFirm

## ADOPT
- **The 9 BMC blocks as the COMPLEMENTARY "what the business IS" map, layered ALONGSIDE Porter's
  "what the business DOES."** Porter decomposes *activities/functions*; BMC decomposes the
  *business logic* (who/what/how-paid). AutoFirm needs both: Porter to assign agent work, BMC to
  parameterize the business per client. **Build implication:** the L2.B2 decomposition engine
  carries a `BusinessModelSpec` (9 typed fields) as the per-client configuration that
  *parameterizes* every downstream playbook (e.g. Revenue Streams → B5 pricing; Customer Segments
  → B7/B8 marketing/sales; Channels → B7; Customer Relationships → B9 support tier design).
- **Key Activities ↔ Porter mapping** is the bridge AutoFirm should encode: BMC "Key Activities"
  is the subset of Porter activities that are *strategically critical for this specific model*.
  The decomposition engine should flag which of the 9 Porter activities are "key" for a given
  client so agent effort concentrates there (avoids uniformly automating low-leverage activities).
- **Production / Problem-solving / Platform** Key-Activity typing is a useful first-order signal
  for *which kind of company* AutoFirm is building (maps loosely to: manufacturing/e-commerce =
  Production; consulting/services = Problem-solving; SaaS/marketplace = Platform) — a clean
  parameterization across the B12 panel.

## REJECT / use-with-care
- **Reject BMC as a process/automation taxonomy.** Its blocks are *strategic descriptors*, not
  executable processes — you cannot "run" a Customer Segment. Use it to *configure* AutoFirm, not
  to assign tasks; APQC PCF (source 03) supplies the executable process layer.
- **Reject treating the 9 blocks as independent.** They are tightly coupled (a VP change ripples to
  CS, CH, RS). AutoFirm's `BusinessModelSpec` validation must enforce cross-block consistency
  (fail-closed, CLAUDE §5.6) rather than letting blocks be set in isolation.

## Concrete build implication
- Component: `function_decomposition/business_model_spec.py` — a typed 9-field dataclass with cross-field validators and an `is_key_activity()` mapping to the Porter taxonomy.
- Test it drives: a property test that every B12 panel industry yields a *complete, internally-consistent* BusinessModelSpec, and that the VP→{CS,CH,RS} coupling validator rejects an inconsistent spec (teeth: mutate a coupled field, assert validation fails).
