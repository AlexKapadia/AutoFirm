# BEST-PARTS — Webster & Wind (1972) + Buygrid

## ADOPT
- **Adopt the Buying-Center role model as AutoFirm's B2B stakeholder data contract.** Every B2B opportunity record must model the DMU explicitly: a list of contacts each tagged with role(s) {Initiator, User, Influencer, Buyer, Decider, Gatekeeper}. This is the structural backbone the agent uses to plan multi-threaded engagement and to "Tailor" (source 04) and identify the "Economic Buyer"/"Champion" (MEDDIC, source 08). *Build implication:* `BuyingCenter` typed contract in L2.B8; the sales agent must map and continuously update DMU roles from public + CRM data before advancing a complex deal.
- **Adopt the Buy-Class switch (New Task / Modified Rebuy / Straight Rebuy) as the top-level motion selector.** New Task = full discovery + Challenger insight + long pipeline; Straight Rebuy = automated reorder / low-touch. This is the single cleanest lever for matching effort to deal type. *Build implication:* `buy_class` field drives which methodology/script the agent deploys.
- **Adopt task + non-task duality:** the agent scores both rational criteria (price/quality/risk) AND individual stakeholder motives (career risk, status) — feeding affect dimension (source 02).

## REJECT
- **Reject applying the full 8-phase Buygrid + 6-role DMU to B2C or transactional sales.** For B2C the DMU collapses (often to one person plus light social influence); forcing the heavyweight B2B model there overfits and wastes effort. The model is explicitly the B2B branch of the B2B-vs-B2C split.

## Why this matters for generality
The role taxonomy is industry-invariant: a manufacturing capex buying center and a healthcare system procurement committee (two B12 rows) have the *same six roles* with different job titles. Parameterize the titles, keep the roles — generality without overfitting.
