# BEST-PARTS — IBCS SUCCESS

## ADOPT
- **SUCCESS as the master rubric for business exhibits/reports** — it unifies Minto (STRUCTURE/SAY), Zelazny (EXPRESS), and Tufte (SIMPLIFY/CHECK) into one governed, checkable standard. Use SUCCESS as the **scoring rubric** the evaluator agent grades generated decks/reports against (generator/evaluator split).
- **UNIFY (semantic notation) as a hard rendering contract:** AutoFirm fixes one consistent visual vocabulary across every artifact for a given company — actual vs plan vs forecast vs prior-year, and variance sign/colour conventions — so all decks/reports decode identically. This is a concrete, testable consistency control (machine-checkable colour/fill mapping).
- **CHECK (visual integrity) as a correctness gate:** no truncated/zero-suppressed axes that mislead, consistent scales across comparable charts. Testable lint -> ties to CLAUDE §3.11 zero-numerical-error / no-misleading-output.
- **CONDENSE + SIMPLIFY:** high information density without chartjunk (reinforces Tufte).

## REJECT
- Treating IBCS as optional styling — adopt it as the *governing rubric*, but allow the per-company brand layer to set palette within IBCS semantic constraints (don't override semantics for cosmetics).

## BUILD IMPLICATION
A `success_rubric` evaluator (7 rules, each a PASS/FAIL check) grades every generated deck/report; a `semantic_notation` config fixes the actual/plan/forecast/variance visual vocabulary per company (UNIFY); a `visual_integrity_lint` enforces CHECK (no misleading axes). These feed the deck/report DoD and `evidence/`. IBCS is the single integrating standard tying sources 06-08 together.
