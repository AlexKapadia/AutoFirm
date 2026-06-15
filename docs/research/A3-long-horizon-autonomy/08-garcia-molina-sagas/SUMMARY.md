# SUMMARY — Garcia-Molina & Salem "Sagas"

## Full citation
- **Title:** Sagas
- **Authors:** Hector Garcia-Molina, Kenneth Salem
- **Year:** 1987
- **Venue:** Proceedings of the 1987 ACM SIGMOD International Conference on Management of Data (SIGMOD 1987), pp. 249–259. Also in ACM SIGMOD Record.
- **DOI:** 10.1145/38713.38742 (proceedings) / 10.1145/38714.38742 (SIGMOD Record)
- **URL:** https://dl.acm.org/doi/10.1145/38713.38742

## Ontology questions informed
- **L1.A3.3** Checkpoint / handoff / resume mechanisms & state externalization (PRIMARY — the foundational long-lived-transaction model).
- Feeds **L2.A3** (resume protocol) and **L2.A8** (data-layer transactional guarantees).

## GRADE tier
- **High.** Peer-reviewed at SIGMOD (top-tier DB venue), foundational and heavily cited; the canonical primary source for the saga/compensation pattern that underpins modern durable-execution and microservice orchestration. No material down-rate.

## Key claims (exact concepts)
- **Problem — Long-Lived Transactions (LLTs):** transactions that "hold on to database resources for relatively long periods of time, significantly delaying the termination of shorter transactions." (Long horizon is the core motivation — directly analogous to long-horizon agent runs.)
- **Saga definition:** "a long-lived transaction that can be written as a sequence of transactions that can be interleaved with other transactions." A saga S is a sequence of sub-transactions T1..Tn.
- **Compensation guarantee:** the DBMS "guarantees that either all the transactions in a saga are successfully completed or compensating transactions [C1..Cn] are run to amend a partial execution." Each Ti has a compensating transaction Ci.
- **Semantic (not physical) undo:** "The compensating step undoes the [step] from a semantic point of view but does not necessarily return the database to the state that existed when the step began" — compensation "restore[s] the world to a state which is an acceptable approximation to the state ... before the start of the transaction."
- Execution sequences: either T1,T2,...,Tn (success) or T1,...,Tj,Cj,...,C1 (partial then compensated).

## Reproducibility note
Concepts (LLT, saga = sequence of sub-transactions with compensations, semantic undo) are quoted from the SIGMOD 1987 paper via independent summaries (ACM DL listing + multiple paper summaries). DOI resolves to the ACM Digital Library. This is the primary anchor for the saga pattern used by sources 10 (SagaLLM) and the durable-execution practitioner literature.
