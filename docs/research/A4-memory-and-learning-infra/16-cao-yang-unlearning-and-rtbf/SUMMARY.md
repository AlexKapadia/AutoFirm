# SUMMARY — Towards Making Systems Forget (Cao & Yang) + the legal right-to-erasure driver

Two independent primaries that together corroborate the **Verified Forgetting (VF)** requirement
from a *different* lineage than SISA (folder 15): one technical-primary, one legal-primary.

## Source A — technical primary
- **Title:** Towards Making Systems Forget with Machine Unlearning
- **Authors:** Yinzhi Cao, Junfeng Yang
- **Year:** 2015
- **Venue:** **IEEE Symposium on Security and Privacy (S&P) 2015**, pp. 463–480 — peer-reviewed,
  top-tier security venue. **This is the paper that coined "machine unlearning."**
- **DOI / URL:** 10.1109/SP.2015.35 — https://dl.acm.org/doi/10.1109/SP.2015.35

### Key claims (faithful)
1. **Coins "machine unlearning"** and frames it as the dual of learning: a system must be able to
   *forget* a data sample's lineage on request.
2. **Summation-form mechanism (exact):** the approach "transform[s] learning algorithms used by a
   system into a summation form. To forget a training data sample, [it] simply updates a small number
   of summations — asymptotically faster than retraining from scratch." Generality comes from
   statistical-query (SQ) learning, "in which many machine learning algorithms can be implemented."
3. **Motivation is privacy/compliance and data-pollution recovery** — the same drivers as AutoFirm's
   VF primitive (delete a tenant's record; roll back a poisoned write).

### GRADE tier
- **High.** Peer-reviewed IEEE S&P; the field-founding primary. Independent of SISA (different
  authors/org/mechanism: summation/SQ-form vs. sharded retraining) — so SISA (15) + Cao-Yang (16A)
  are **two independent primaries**, not one study cited twice.

## Source B — legal primary (the *why deletion must be verifiable*)
- **Title:** Regulation (EU) 2016/679 (GDPR), **Article 17 — "Right to erasure ('right to be
  forgotten')"**; supported by Article 5(1) and the storage-limitation principle.
- **Authors/Org:** European Parliament & Council of the EU
- **Year:** 2016 (in force 2018)
- **Venue:** Official Journal of the EU — **primary legislative text**
- **URL:** https://eur-lex.europa.eu/eli/reg/2016/679/oj (Art. 17 at
  https://gdpr-info.eu/art-17-gdpr/)

### Key claims (faithful)
1. **Art. 17(1):** "The data subject shall have the right to obtain from the controller the erasure
   of personal data concerning him or her without undue delay" on specified grounds.
2. A compliance obligation to erase implies an obligation to be **able to demonstrate** erasure
   (accountability principle, Art. 5(2)) — i.e. deletion must be *verifiable*, not asserted. This is
   the legal basis for AutoFirm's VF "auditable non-recoverability proof."
3. Parallel US driver: **CCPA/CPRA right to delete** (Cal. Civ. Code §1798.105) — same obligation,
   independent jurisdiction.

### GRADE tier
- **High (for the legal claim).** Primary legislative text; the authoritative source for the erasure
  obligation. Indirect for the *technical* claim, so used only to justify *why* VF must exist, never
  as evidence for any deletion *mechanism*.

## Questions informed
- **L1.A4.4** Memory security & governance — VF primitive (technical feasibility + legal necessity).

## Reproducibility note
Cao–Yang summation/SQ mechanism is in the paper body (S&P 2015, §III); GDPR Art. 17 text is verbatim
at EUR-Lex. Both re-derivable at the URLs.
