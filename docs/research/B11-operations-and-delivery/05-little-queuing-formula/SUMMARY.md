# SUMMARY — Little's Law (queueing / flow fundamental)

## Full citation
- **Primary:** Little, John D. C. (1961). *A Proof for the Queuing Formula: L = λW.* **Operations
  Research, 9(3): 383–387.** DOI: 10.1287/opre.9.3.383.
- **50th-anniversary review (primary author):** Little, J. D. C. (2011). *Little's Law as Viewed on
  Its 50th Anniversary.* Operations Research, 59(3): 536–549. DOI: 10.1287/opre.1110.0940.
  Reprint — https://people.cs.umass.edu/~emery/classes/cmpsci691st/readings/OS/Littles-Law-50-Years-Later.pdf
- **Corroborating reference:** Wikipedia "Little's law" — https://en.wikipedia.org/wiki/Little's_law

## Ontology questions informed
- **L1.B11.1** (primary): operations/flow math. Feeds **L2.B11** and **L2.B4.3** (capacity/throughput/queueing modeling).

## GRADE tier
- **High.** A peer-reviewed mathematical theorem in *Operations Research* (top OR journal) with a
  formal proof, 2,700+ citations, re-affirmed by the author at 50 years. Theorems do not weaken;
  up-rated for being a proven invariant, not an empirical effect.

## Key claims (faithful, formula EXACT)

### The law
> **L = λW**

where (Little, 1961; 2011):
- **L** = the long-term **average number of items (customers) in the system** (i.e., average
  inventory / WIP / queue length).
- **λ** (lambda) = the long-term **average effective arrival rate** (throughput, items per unit time)
  — in steady state, arrival rate = departure rate.
- **W** = the **average time an item spends in the system** (flow time / lead time / cycle time).

### Generality (why it matters)
- Holds under **broad stationarity** ("stable") conditions: the long-run averages must exist, the
  system boundary must be consistent, and λ must match the population whose time W is measured.
- **Distribution-free:** does NOT assume Poisson arrivals or exponential service; independent of the
  arrival process, the service-time distribution, AND the queue discipline (FIFO, LIFO, etc.).
- Applies to **systems within systems** (any well-defined boundary).

### Equivalent operations form (manufacturing / flow)
> **WIP = Throughput × Cycle Time**  →  **Cycle Time = WIP / Throughput**

Worked examples (from the law, exact): retail with λ=10 arrivals/hr and W=0.5 hr → **L = 5**;
a line producing 200 units/day with WIP=100 → cycle time = 100/200 = **0.5 day**.

## Reproducibility note
The formula and proof are in Little (1961), Operations Research 9(3):383–387. The distribution-free
generality and worked examples are confirmed in Little (2011) and the cited reference. Any reviewer
can re-derive L=λW directly from those primary papers.
