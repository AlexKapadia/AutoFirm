# BEST-PARTS - OPM Competency Gap Analysis

## ADOPT
1. **Target-minus-current proficiency as the skill-gap formula.** AutoFirm's SKILL_GAP detection
   = `gap = target_proficiency(competency) - current_proficiency(competency)`. The role charter
   declares target proficiencies (via its `must_study` set); the roster's current agents declare
   what they have studied; the diff is the gap.
2. **Mission-critical-occupation-first targeting.** Don't run gap-detect uniformly. AutoFirm
   prioritises gaps on the **critical path of the manager's objective** (the MCO analogue), so
   spawn/onboard effort goes where it moves the mission. ADOPT as the gap-detector's ranking rule.
3. **The hire / train / reassign remedy menu.** Every detected gap maps to exactly one of three
   bridge actions: **spawn** (hire), **onboard/study** (train), or **redeploy** (reassign an
   existing agent). ADOPT this as the closed remedy set so the engine never invents ad-hoc fixes.

## REJECT
- **Federal RIF legal machinery / tenure-and-veteran-preference ordering** (from the companion
  reshaping handbook) - jurisdiction-specific employment law, irrelevant to agent retirement.
  REJECT the legal procedure; keep only the *redeploy-before-eliminate* principle (see source 10).

## Build implication
- **Component:** `org-engine/gap-detector` (skill-gap branch) + `role-charter` schema
  (`must_study: competency[] with target_proficiency`).
- **Contract test:** given a charter's target competencies and the current roster's competencies,
  the detector emits a SKILL_GAP iff target > current for some required competency, ranked by
  critical-path weight - deterministic and unit-testable.
