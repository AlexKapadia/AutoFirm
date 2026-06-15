# BEST-PARTS — McCabe Cyclomatic Complexity

## ADOPT
1. **Objective complexity gate alongside the file-size rule.** CLAUDE.md §5.7 already mandates <=300-line files; add **v(G) = E - N + 2P** per function as a second, behaviour-aware signal. A high-v(G) function is hard to test (it implies many independent paths needing coverage) — AutoFirm flags functions above a threshold (McCabe's heuristic ~10) for decomposition, in addition to the line limit.
2. **Use v(G) to size the test budget, not just to refactor.** Because v(G)+1 lower-bounds the number of independent paths, AutoFirm can use it to *predict how many tests/properties a function needs*, feeding the test generator.
3. **Combine with the §5.7 naming/one-responsibility rules** — a function with high v(G) usually violates single-responsibility; the metric operationalises "this file needs splitting".

## REJECT / BOUND
- **Reject v(G) as a sole quality oracle.** Shepherd's critique and mixed defect-correlation replications show v(G) largely tracks size and is context-dependent. Use it as a *trigger for review*, never as an automated pass/fail on its own. The threshold (10) is a heuristic, configurable per language/project.

## Concrete artifact this drives
- A `code-org gate` combining: file <=300 lines (CLAUDE.md §5.7), per-function v(G) <= configurable threshold (default ~10, advisory), and self-documenting-name lint. v(G) also seeds the minimum test/property count for the function in the test generator.
