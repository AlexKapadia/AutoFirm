# SYNTHESIS — B6 Fundraising & capital structure foundations (L1.B6.1)

**Scope:** the literature foundations for how companies are funded — the **capital-structure
theory** that explains *why* one instrument is preferred over another, and the **instrument menu**
(equity, debt, grants) with **stage norms**. Feeds L2.B6 (the automated fundraising & capital
playbook). Public-data only; no PII (CLAUDE.md §3.12).

## The alternative space surveyed (full menu, then judged)

### A. Capital-structure THEORY (why instrument choice matters at all)
| Theory | Source | Core claim | ADOPT/REJECT for AutoFirm |
|---|---|---|---|
| Irrelevance (MM 1958/63) | 01 | In a frictionless world, structure does not change value; V_L = V_U + T_C*D once taxes added | ADOPT as **baseline/frame** only; REJECT as a recommendation |
| Trade-off (Kraus-Litzenberger 1973) | 02 | Optimal leverage balances tax shield vs. distress cost; a target band exists | ADOPT as **debt-capacity ceiling** for established firms; REJECT for pre-profit startups |
| Pecking order (Myers / Myers-Majluf 1984) | 03 | Asymmetric info -> internal > debt > equity hierarchy | ADOPT as **default ordering for opaque/early-stage**; REJECT as a hard law |
| Empirical adjudication (Frank-Goyal 2009) | 04 | 6 reliable factors; data "reasonably consistent with trade-off"; profit-leverage negative keeps pecking order alive | ADOPT the **factor set + hybrid verdict** |

**Verdict (hybrid, per CLAUDE.md §3.5):** no single theory wins universally. AutoFirm should run a
**hybrid**: pecking-order *ordering* (internal -> non-dilutive -> debt -> equity) as the prior for
opaque/early-stage clients, with a **trade-off target leverage band** (anchored on industry-median
leverage + tangibility/profitability/size from Frank-Goyal) for established, asset-holding clients.
MM is the frame that forces every choice to be justified by a named friction.

### B. The INSTRUMENT MENU + stage norms (what to actually raise, when)
| Instrument | Source | Dilution | Best-fit stage / profile |
|---|---|---|---|
| Insider / friends & family / angels | 05 | High (equity) | Infant, information-opaque, pre-revenue |
| SAFE / convertible (post-money) | 07 | Equity (deferred) | Pre-seed/seed; 70%+ of pre-seed deals |
| Priced equity round (convertible preferred) | 06, 07 | High; 5-rights bundle | Seed -> Series A+; needs the full term-sheet model |
| Grants (SBIR/STTR) | 08 | **Zero** | US small-biz R&D / deep-tech; eligibility-gated |
| Revenue-based financing | 08 | **Zero** | Predictable recurring revenue (SaaS, marketplace) |
| Venture debt | 08 | Low (~0.1-1.0% warrants) | Series A+, traction + VC backing; runway extension |
| Bank / intermediated debt, public debt/equity | 05 | Low/none | Mature, transparent, asset-holding firms |

**Stage norms (Carta, dated benchmarks — source 07):** pre-seed ~$0.75-1.5M on ~$10-15M SAFE cap;
seed median post-money $24M (Q4 2025), ~20-25% dilution; Series A median post-money $78.7M (Q4 2025),
~17.9% dilution (Q1 2025). Trend: per-round dilution falling (~18% -> ~16%). **These are
refreshable benchmarks, never constants.**

## Concrete recommendation for AutoFirm (the build implication)

The L2.B6 fundraising playbook is a **two-layer, hybrid, deterministic engine**, all paths
unit-exact and self-explaining (CLAUDE.md §3.11), industry-parameterized for B12:

1. **`growth_cycle_stage_classifier`** (source 05) — age/size/assets/opacity -> stage label.
2. **`financing_source_ranker`** (sources 03, 05, 08) — pecking-order prior, re-weighted by stage,
   revenue profile, dilution tolerance, and **eligibility predicates** for grants/RBF/venture debt
   (fail-closed: unknown eligibility -> not recommended).
3. **`capital_structure_analyzer` + `leverage_benchmark`** (sources 01, 02, 04) — for debt-capable
   clients: tax shield minus distress cost -> target leverage band, anchored on industry-median
   leverage; reproduces Frank-Goyal signs.
4. **`dilution_engine` + `term_sheet_model`/`explainer`** (sources 06, 07) — exact post-money-SAFE
   conversion (`ownership = investment / post_money_cap`), multi-round cap-table projection, and the
   **five-rights** term-sheet model (liquidation preference, participation, control) so offers are
   compared on true cost, not headline valuation.
5. **`round_benchmark_check`** (source 07) — flags out-of-range asks against a **date-stamped**
   benchmark table that is re-pulled, never hard-coded.

**Generality proof obligation (CLAUDE.md §4.5, §3.9):** every recommendation must be sensible for all
8 B12 panel rows — e.g. a B2C restaurant correctly sees *no* SBIR/RBF and bank-debt-led financing,
while a US deep-tech SaaS sees SAFE -> SBIR -> RBF -> venture debt. Overfitting to one example fails.

**Security/data (CLAUDE.md §3.12, §5.6):** all benchmarks are PUBLIC data; client financials live in
the gitignored private workspace (L1.A6.4 / L1.B4.4); fail-closed on eligibility and on missing data.

## Source-count / GRADE compliance (DEPTH-RUBRIC §1-2)

- **Capital-structure theory (important/critical claims):** corroborated by >=3 High-tier
  peer-reviewed sources (01 MM, 02 Kraus-Litzenberger, 03 Myers/Myers-Majluf, 04 Frank-Goyal).
- **Formulae (correctness-critical):** MM Prop. I/II and V_L = V_U + T_C*D reproduced exactly with
  notation (source 01); trade-off and SAFE-conversion formulae stated exactly.
- **Stage-norms numbers:** industry-primary (Carta, Moderate) cited **with as-of dates**; flagged as
  refreshable, not constants. Grant caps: government-primary with effective date. RBF/venture-debt
  exact figures: Low tier -> used for mechanics only, not as sole quantitative basis.

## Open items for the QA / L2 stage
- Add a peer-reviewed source on **venture debt** and **RBF** specifically (current 08 leans
  vendor/practitioner — Low tier) before any *quantitative* RBF/venture-debt claim is relied upon.
- Validate Carta medians against a second independent dataset (e.g. PitchBook/NVCA) for non-Carta
  selection bias before the benchmark feed is trusted.
