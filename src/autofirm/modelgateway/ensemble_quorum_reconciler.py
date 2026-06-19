"""PURE ensemble reconciliation: marginalize N model answers into one verdict.

What this does
--------------
Implements the deterministic aggregation half of ``ensemble_quorum`` (ADR-003 §3),
faithful to Self-Consistency (Wang et al., ICLR 2023 — ``docs/research/B1.../
2023-self-consistency-majority-vote``): take the **majority vote** over the members'
answers,

    arg max_a  sum_i  indicator(answer_i == a)

with a DETERMINISTIC tie-break so the verdict never depends on dict/order
nondeterminism. Two clearly-separated paths:

* :func:`reconcile_exact_majority` — for ``extract`` / ``classify`` / ``route`` where
  answers are exact strings/labels. Members may be sampled, but their answers are
  compared by exact equality; ties break by INPUT order (the caller supplies answers
  in call-plan/candidate order), so one corrupted/minority answer can never flip a
  clear majority and the verdict is deterministic.
* :func:`reconcile_free_text` — the explicitly-flagged free-text path: members may be
  sampled at ``T>0`` (diverse phrasings), but the aggregation is still deterministic
  — answers are normalised then exact-majority-voted under a PINNED comparison, so
  the same multiset of answers always yields the same verdict in replay.

Why it exists / where it sits
-----------------------------
``data-contracts.md`` §7 / B1 self-consistency: quorum aggregation must be
deterministic even when members are stochastic. Keeping it pure (no I/O, no clock)
lets it be metamorphic-tested (permuting equal answers must not change the verdict;
one corrupted answer must not flip a clear quorum) — CLAUDE.md §3.6.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Determinism (§3.11):** verdict is a pure function of ``answers``; ties break by
  the earliest input (call-plan) index, never by hash/dict-insertion order.
* **Quorum integrity:** a verdict is returned only if its vote count reaches the
  required ``quorum``; below quorum the reconciler refuses (no quorum, no verdict).
* **One bad member cannot flip a clear majority:** votes are counted by exact value,
  so a single corrupted/minority answer is outvoted, never amplified.
"""

from __future__ import annotations

__all__ = [
    "QuorumNotReached",
    "reconcile_exact_majority",
    "reconcile_free_text",
]


class QuorumNotReached(RuntimeError):
    """Raised when no single answer reaches the required quorum (fail-closed).

    A split with no answer meeting the threshold is NOT silently resolved to a
    plurality winner — the reconciler refuses, so a weak quorum never ships as a
    confident verdict.
    """


def _majority_by_first_support(answers: tuple[str, ...], quorum: int) -> str:
    """Return the exact-majority answer (>= quorum votes); ties break by input order.

    Votes are counted by exact string equality. Among the answers with the highest
    (and quorum-meeting) vote count, the winner is the one whose FIRST supporting
    member appears earliest in INPUT order. The caller passes answers in
    candidate/call-plan order, so "earliest input" == "highest-priority candidate"
    — a deterministic, replay-stable tie-break. Raises :class:`QuorumNotReached`
    if the top vote count is below ``quorum``.
    """
    if quorum <= 0:
        # fail-closed: a non-positive quorum is a malformed aggregation request.
        raise ValueError("quorum must be a positive integer")
    if not answers:
        # fail-closed: there is nothing to reconcile — refuse rather than invent one.
        raise QuorumNotReached("no answers to reconcile")

    # Count votes by exact value; record each answer's EARLIEST supporting index.
    # The caller passes answers in candidate/call-plan ORDER, so the earliest
    # supporting index IS the priority of the highest-priority candidate that
    # produced that answer — a deterministic, replay-stable tie-break key.
    counts: dict[str, int] = {}
    first_support_index: dict[str, int] = {}
    for index, answer in enumerate(answers):
        counts[answer] = counts.get(answer, 0) + 1
        if answer not in first_support_index:
            first_support_index[answer] = index

    top = max(counts.values())
    if top < quorum:
        # fail-closed: no answer reached the agreed quorum — refuse a weak verdict.
        raise QuorumNotReached(
            f"top answer has {top} vote(s); quorum {quorum} not reached"
        )

    # Among the top-voted answers, the winner is the one whose first supporter is
    # earliest in input (candidate/plan) order — fully deterministic and replay-stable.
    winners = [answer for answer, count in counts.items() if count == top]
    winners.sort(key=lambda a: first_support_index[a])
    return winners[0]


def reconcile_exact_majority(answers: tuple[str, ...], quorum: int) -> str:
    """Majority-vote exact answers (extract/classify/route); ties break by call order.

    Answers are compared verbatim (no normalisation). When two answers tie on votes,
    the one whose first supporter is earliest in the input (the higher-priority
    candidate from the call plan) wins — a deterministic, replay-stable rule.
    """
    return _majority_by_first_support(answers, quorum)


def reconcile_free_text(answers: tuple[str, ...], quorum: int) -> str:
    """Deterministically reconcile free-text answers (members may be sampled T>0).

    Members may produce diverse phrasings, so each answer is NORMALISED (whitespace
    collapsed, case-folded) before the exact-majority vote — but the aggregation is
    still deterministic: the same multiset of normalised answers always yields the
    same verdict, and the ORIGINAL text of the winning normalised group is returned
    (the first input member that produced it), so the verdict is replay-stable.
    """
    if not answers:
        raise QuorumNotReached("no answers to reconcile")

    # Normalise for comparison only; keep a map back to the original text of the
    # first member (in input order) that produced each normalised form.
    def _normalise(text: str) -> str:
        # The join SEPARATOR content is unobservable: this normalised string is
        # only ever a comparison KEY (the function returns the ORIGINAL text, never
        # this value), so any non-empty separator groups identically. The split()
        # collapse and casefold() ARE tested (load-bearing).
        return " ".join(text.split()).casefold()  # pragma: no mutate

    normalised = tuple(_normalise(a) for a in answers)
    original_for_norm: dict[str, str] = {}
    # strict=True is a defensive guard; answers and normalised are built 1:1 so a
    # length mismatch is impossible here -> strict True/False is behaviourally equal.
    for original, norm in zip(answers, normalised, strict=True):  # pragma: no mutate
        if norm not in original_for_norm:
            original_for_norm[norm] = original

    winning_norm = _majority_by_first_support(normalised, quorum)
    # Return the ORIGINAL text of the winning group (deterministic: the first input
    # member that produced this normalised form), not the lower-cased comparison key.
    return original_for_norm[winning_norm]
