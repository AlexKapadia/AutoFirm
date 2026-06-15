# SUMMARY — Is Mutation an Appropriate Tool for Testing Experiments?

## Full citation
- **Title:** Is Mutation an Appropriate Tool for Testing Experiments?
- **Authors:** James H. Andrews, Lionel C. Briand, Yvan Labiche
- **Year:** 2005
- **Venue:** Proceedings of the 27th International Conference on Software Engineering (ICSE 2005),
  pages 402-411
- **DOI/URL:** 10.1109/ICSE.2005.1553583 | https://dblp.uni-trier.de/rec/conf/icse/AndrewsBL05.html

## Questions informed
- **L1.A9.3** Mutation testing -- the EMPIRICAL VALIDATION that mutants are a valid fault proxy
  (PRIMARY/High). This is the critical-claim corroboration for using mutation score as evidence.

## GRADE tier: High
Peer-reviewed ICSE (flagship SE conference). Controlled empirical study using programs with
comprehensive test pools and known real faults. The load-bearing finding (mutants resemble real
faults) is exactly the kind of controlled-study evidence DEPTH-RUBRIC §2 rates High.

## Key claims

### Research question and method
Asks whether using *generated mutants* as a stand-in for *real faults* in testing experiments
yields valid, representative conclusions. Method: programs with comprehensive pools of test cases
AND known (real, hand-seeded/historical) faults; compare how test suites' fault-detection on real
faults relates to their mutant-detection.

### Main finding
"the use of mutation operators is yielding trustworthy results [...] generated mutants [are]
similar to real faults" for the purpose of assessing test-suite effectiveness. Specifically, the
detection ratios of mutants are a reasonable predictor of the detection ratios of real faults --
so a test suite's mutation score is a valid proxy for its real-fault detection ability.

### Important caveat (faithfully recorded)
The paper also finds that **hand-seeded faults** (faults manually inserted by people) are LESS
representative / can be harder to detect than real faults and than mutants -- i.e. mutants are a
*better* experimental proxy than hand-seeded faults. This nuance matters: mutation > manual fault
seeding for experimental validity.

## Reproducibility note
Finding extracted from the ICSE 2005 abstract/summary (University of Limerick, Semantic Scholar,
Simula listings) which consistently report the "mutants similar to real faults / trustworthy"
conclusion and the hand-seeded-faults caveat. This is a *critical claim* (it justifies treating
mutation score as evidence of real quality); per DEPTH-RUBRIC §1 it is corroborated by Offutt's
coupling-effect work (in source 07) and Google's empirical productive-mutant data (source 09),
giving >=3 independent supports.
