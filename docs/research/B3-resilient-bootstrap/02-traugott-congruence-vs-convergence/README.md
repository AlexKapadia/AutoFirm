# Traugott — Congruence vs. Convergence vs. Divergence ("Why Order Matters")

> Research note for AutoFirm CRO research org. Workstream **B3 — Resilient Bootstrap**.
> Bar: institution-grade, primary-sourced, exact citation, faithful reproduction (CLAUDE.md §3.3, §4.6).

---

## 1. Full citation

Steve Traugott and Lance Brown, *"Why Order Matters: Turing Equivalence in Automated Systems Administration"*. In **Proceedings of the 16th USENIX Systems Administration Conference (LISA '02)**, Philadelphia, PA, USENIX Association, November 2002, pp. 99–120.
- USENIX landing: <https://www.usenix.org/conference/lisa-02/why-order-matters-turing-equivalence-automated-systems-administration>
- Author full text (canonical): <http://www.infrastructures.org/papers/turing/turing.html>
- ACM DL: <https://dl.acm.org/doi/10.5555/1050517.1050529>

Defines the **divergent / convergent / congruent** taxonomy of infrastructure state, and argues from a Turing-machine equivalence that **deterministic ordering of changes** is necessary to predictably administer an enterprise infrastructure. Directly references and contrasts with Burgess's CFEngine convergence (see sibling note `01-burgess-cfengine-convergence`).

---

## 2. Faithful structured summary (definitions reproduced exactly)

### 2.0 The taxonomy
> *"[host configurations can be] classified into one of three categories: divergent, convergent, and congruent."* (§4)

### 2.1 Divergence — reproduced verbatim (§4.1)
> *"Divergence (figure 4.1.1) generally implies bad management… Divergence is characterized by the configuration of live hosts drifting away from any desired or assumed baseline disk content."*

Detection test (verbatim):
> *"One quick way to tell if a shop is divergent is to ask how changes are made on production hosts, how those same changes are incorporated into the baseline build for new or replacement hosts, and how they are made on hosts that were down at the time the change was first deployed. If you get different answers, then the shop is divergent."*

Causes (verbatim): *"that class of operations that create non-reproducible change… ad-hoc manual changes, changes implemented by two independent automatic agents on the same host, and other unordered changes."* Symptoms: *"unpredictable host behavior, unscheduled downtime… 'firefighting', and high troubleshooting and maintenance costs."*

### 2.2 Convergence — reproduced verbatim (§4.2)
> *"Convergence (figure 4.2.1) is the process most senior systems administrators first begin when presented with a divergent infrastructure… Convergence is characterized by the configuration of live hosts moving towards an ideal baseline. By definition, all converging infrastructures are still diverged to some degree."*

The check-then-act mechanism (verbatim) — note this is Traugott's plain-English statement of Burgess's convergent operator:
> *"Convergent tools typically work by sampling a small subset of the disk — via a checksum of one or more files, for example — and taking some action in response to what they find. The samples and actions are often defined in a declarative or descriptive language… This emulates and preempts the firefighting behavior of a reactive human systems administrator — 'see a problem, fix it'."*

Attribution (verbatim): *"Convergence is a feature of Mark Burgess' Computer Immunology principles. His cfengine is in our opinion the best tool for this job."*

Key limitation (verbatim) — convergence manages only a *subset* of disk, so it can never prove completeness:
> *"Because convergence typically includes an intentional process of managing a specific subset of files, there will always be unmanaged files on each host… an attempt to converge formerly divergent hosts to an ideal configuration is a never-ending process."*

### 2.3 Congruence — reproduced verbatim (§4.3)
> *"Congruence (figure 4.3.1) is the practice of maintaining production hosts in complete compliance with a fully descriptive baseline. Congruence is defined in terms of disk state rather than behavior, because disk state can be fully described, while behavior cannot."*

The boundary with convergence (verbatim, from §4.2):
> *"If an infrastructure maintains full compliance with a fully descriptive baseline, then it is congruent according to our definition, not convergent."*

How congruence is achieved (verbatim): an infrastructure *"based upon first loading a known baseline configuration on all hosts, and limited to purely orthogonal and non-interacting sets of changes, implements congruence."*

Failure handling under congruence (verbatim) — fail-closed / rebuild:
> *"By definition, divergence from baseline disk state in a congruent environment is symptomatic of a failure of code, administrative procedures, or security… It is usually safe to handle all three cases as a security breach: correct the root cause, then rebuild."*

Detection test (verbatim): *"ask how the oldest, most complex machine in the infrastructure would be rebuilt if destroyed. If years of sysadmin work can be replayed in an hour, unattended, without resorting to backups… then host management is likely congruent."*

### 2.4 Convergence vs. congruence — the trade-off (verbatim)
> *"Convergence features also provide more adaptive self-healing ability than pure congruence, due to a convergence tool's ability to detect when deviations from baseline have occurred. Congruent infrastructures rely on monitoring to detect deviations, and generally call for a rebuild when they have occurred."*

And the limit (verbatim): *"We know of no previously divergent infrastructure that, through convergence alone, has reached congruence."*

### 2.5 The central thesis — order & determinism (§2, §3)
> *"It appears that a tool that produces deterministic order of changes is cheaper to use than one that permits more flexible ordering. The unpredictable behavior resulting from unordered changes to disk is more costly to validate than the predictable behavior produced by deterministic ordering."* (§2)

The prediction (verbatim, §3):
> *"The least-cost way to ensure that the behavior of any two hosts will remain completely identical is to always implement the same changes in the same order on both hosts."*

Turing-equivalence framing (verbatim, abstract/§1): a self-administered host is *"equivalent to a Turing machine"*; *"no tool can predictably administer an enterprise infrastructure without maintaining a deterministic, repeatable order of changes on each host."* The circular-dependency hazard (§2): *"A 'circular dependency' or control-loop problem exists when an administrative tool executes code that modifies the tool or the tool's own foundations (the underlying host)."*

### 2.6 Idempotence note
Traugott does not center the word "idempotence"; he expresses the same property operationally — convergent tools sample-then-act so repeated runs are safe, and congruence is reached by replaying *the same orthogonal changes in the same deterministic order*. Idempotence in this paper is a property of the *ordered, reproducible build*, not of an individual unordered command.

---

## 3. Best-parts-to-take — mapped to the W3 resilient-bootstrap design

W3's bootstrap sits deliberately **between Burgess's convergence and Traugott's congruence**: it uses per-step convergent `check()→apply()` (Burgess) to self-heal, while striving toward a Traugott **fully-descriptive baseline** for the small, fully-managed capability set the platform owns.

### 3.1 `bootstrap_step.check() → apply()` = Traugott's "sample, then act" (justifies the contract)
Traugott's plain-English convergent mechanism — *"sampling a small subset… and taking some action in response to what they find… 'see a problem, fix it'"* — is exactly the W3 `check() -> already_applied?` then conditional `apply()`. This independently corroborates the Burgess fixed-point justification (sibling note §3.1): the **observe/sample is mandatory before any mutating action**, which is what makes the bootstrapper a re-runnable no-op on an already-compliant environment.

### 3.2 W3 manages a *fully descriptive baseline* for its OWN capability set → aim for congruence, not endless convergence
Traugott's critical limitation: convergence over an *unmanaged-superset* disk is *"a never-ending process"* and can never prove completeness. **Design implication:** scope W3's bootstrap to a **small, fully-enumerated, fully-descriptive baseline** of the capabilities the platform actually owns (interpreters, dirs, keys, services). Within that enumerated set the bootstrap can be **congruent** (provably complete: a destroyed environment *"can be replayed… unattended, without resorting to backups"*), not merely convergent. Do not let it sprawl into managing an open-ended subset of the host.

### 3.3 `degraded_mode_policy` = Traugott's fail-closed "treat as breach, then rebuild" — scoped to one capability
Traugott: a deviation in a congruent environment is *"symptomatic of a failure of code, administrative procedures, or security… safe to handle all three cases as a security breach: correct the root cause, then rebuild."* W3 mapping: when a `bootstrap_step` cannot reach its baseline state, `degraded_mode_policy` **fails that capability closed** (refuse to expose a half-built capability — CLAUDE.md §5.6) and marks it for **rebuild/re-converge on the next run**, while the platform stays up degraded. This blends Burgess's "keep running, self-heal later" with Traugott's "don't trust a deviated state — rebuild it cleanly," scoped to a capability rather than the whole host.

### 3.4 Deterministic ordering of dependent steps (the thesis)
Traugott's core result — *"the same changes in the same order"* — maps to W3 declaring an **explicit, deterministic dependency order** for non-orthogonal `bootstrap_step`s, and keeping orthogonal steps order-free (consistent with Burgess §2.6). This gives W3 the predictability/determinism the suite tests for, and avoids the circular-dependency control-loop hazard when a step modifies the platform's own foundations (§2.5).

### 3.5 `doctor` report = Traugott's "monitoring to detect deviations from baseline"
Traugott: *"Congruent infrastructures rely on monitoring to detect deviations."* The W3 `doctor` report **is** that monitor: a read-only pass that samples each capability's state against its descriptive baseline and reports `congruent | degraded | failed` with the deviation and root cause — the audit surface that decides when a rebuild/re-converge is warranted.

### 3.6 Self-healing convergence + congruent baseline = the W3 sweet spot
Traugott §4.2: convergence gives *"more adaptive self-healing ability than pure congruence."* W3 keeps that self-healing (re-run converges a partial environment) **and** the congruent baseline's reproducibility (fully-descriptive, rebuildable capability set) — getting both rather than choosing one.

---

## One-line takeaway
Traugott's taxonomy — **divergence** (drift from baseline), **convergence** (sample-then-act moving *toward* an incomplete baseline), **congruence** (full, deterministic, reproducible compliance with a *fully descriptive* baseline) — tells W3 to scope its bootstrap to a small fully-described capability set it can keep *congruent* via convergent `check()→apply()`, ordering dependent steps deterministically and failing any unreachable capability closed for rebuild.
