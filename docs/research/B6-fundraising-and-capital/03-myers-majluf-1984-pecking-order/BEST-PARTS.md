# BEST-PARTS — Myers (1984) & Myers-Majluf (1984)

## ADOPT

- **Adopt the financing hierarchy as the DEFAULT ordering for opaque / early-stage clients:**
  internal funds -> debt -> external equity. This is the right prior precisely where information
  asymmetry is highest (startups), and it dovetails with Berger-Udell's growth cycle (source 05).
- **Adopt the adverse-selection insight as an explainability rule:** when the engine recommends
  *against* an equity raise (or recommends debt/non-dilutive first), it can cite the dilution +
  signaling cost of issuing equity under asymmetric information — a self-justifying explanation
  (CLAUDE.md §3.11).
- **Adopt the "profitable firms borrow less" prediction** as a sanity check: a profitable,
  cash-generative client should be steered toward internal funding / minimal external capital before
  any raise is recommended.

## REJECT

- **Reject the pecking order as a hard universal law.** Frank-Goyal (source 04) show large firms with
  assets actually exhibit trade-off-style target leverage; and high-growth startups deliberately
  raise equity *despite* the pecking order because they have no internal funds and need to fund
  growth they cannot debt-finance. So the hierarchy is a **prior, overridden by growth needs and
  asset profile**, not an absolute.

## Concrete build implication

- **Component:** `financing_source_ranker` — orders the instrument menu (internal, grant, RBF,
  venture debt, equity) with pecking-order as the base prior, then re-weighted by stage (source 05),
  revenue profile, and growth ambition.
- **Contract:** output is a ranked list with a cited rationale per item (which friction drove the
  ranking), feeding the explainability report.
- **Test:** a profitable steady-state client ranks internal/debt above equity; a pre-revenue
  high-growth client correctly inverts toward equity/grants — proving the prior is overridden by
  inputs, not hard-coded (generality, CLAUDE.md §3.9).
