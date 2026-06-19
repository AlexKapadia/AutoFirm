"""Metamorphic + fail-closed tests for the PURE ensemble quorum reconciler.

Metamorphic properties (CLAUDE.md §3.6): permuting equal answers does not change the
verdict; one corrupted/minority answer can NEVER flip a clear quorum; the priority
tie-break is deterministic and replay-stable. Plus fail-closed: a below-quorum split
is refused, never resolved to a plurality.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.modelgateway.ensemble_quorum_reconciler import (
    QuorumNotReached,
    reconcile_exact_majority,
    reconcile_free_text,
)

_LABELS = st.sampled_from(["A", "B", "C", "D"])


@pytest.mark.property
@given(answers=st.lists(_LABELS, min_size=1, max_size=9), data=st.data())
def test_permuting_answers_does_not_change_the_verdict(
    answers: list[str], data: st.DataObject
) -> None:
    quorum = max(1, (len(answers) // 2) + 1)
    permutation = data.draw(st.permutations(answers))
    try:
        verdict = reconcile_exact_majority(tuple(answers), quorum)
    except QuorumNotReached:
        # a permutation of the SAME multiset must also fail to reach quorum.
        with pytest.raises(QuorumNotReached):
            reconcile_exact_majority(tuple(permutation), quorum)
        return
    # When a quorum exists, a permutation of the same multiset yields the same verdict
    # (the priority tie-break uses input order, so only run this when there is a clear
    # majority — i.e. exactly one answer reaches quorum, making it permutation-stable).
    counts = {a: answers.count(a) for a in set(answers)}
    if sum(1 for c in counts.values() if c >= quorum) == 1:
        assert reconcile_exact_majority(tuple(permutation), quorum) == verdict


@pytest.mark.property
@given(
    majority_votes=st.integers(min_value=3, max_value=6),
    corrupt=st.text(min_size=1, max_size=8),
)
def test_one_corrupted_answer_cannot_flip_a_clear_quorum(
    majority_votes: int, corrupt: str
) -> None:
    # A clear majority for "GOOD"; one corrupted minority answer is added.
    answers = tuple(["GOOD"] * majority_votes + [corrupt])
    quorum = majority_votes  # GOOD meets it; the single corrupt answer cannot.
    if corrupt == "GOOD":
        # not a corruption — it just strengthens the majority.
        assert reconcile_exact_majority(answers, quorum) == "GOOD"
        return
    assert reconcile_exact_majority(answers, quorum) == "GOOD"


@pytest.mark.unit
def test_priority_tie_break_is_deterministic() -> None:
    # A 1-1 tie between A and B with quorum 1; priority order decides deterministically.
    answers = ("A", "B")
    # A appears first (index 0) so it wins the tie on first-support index.
    assert reconcile_exact_majority(answers, quorum=1) == "A"
    # Same multiset, B first -> B wins. Verdict tracks the deterministic rule, not luck.
    assert reconcile_exact_majority(("B", "A"), quorum=1) == "B"


@pytest.mark.unit
def test_tie_break_tracks_first_support_index_through_a_multiway_tie() -> None:
    # A 3-way 1-1-1 tie (quorum 1): the winner is the answer whose FIRST supporter is
    # earliest in input (call-plan) order. This pins the exact sort key — a mutant
    # that sorts by anything other than first_support_index (e.g. reversed, by count
    # only, by answer text) would pick a different winner here.
    assert reconcile_exact_majority(("C", "A", "B"), quorum=1) == "C"  # C first
    assert reconcile_exact_majority(("B", "C", "A"), quorum=1) == "B"  # B first
    # A repeated earlier answer keeps its FIRST index, so it still wins a tie against a
    # later distinct answer with the same vote count.
    assert reconcile_exact_majority(("A", "B", "A", "B"), quorum=2) == "A"


@pytest.mark.unit
def test_below_quorum_split_is_refused_fail_closed() -> None:
    # 1-1-1 three-way split, quorum 2 -> no answer reaches it -> refuse.
    # Anchored exact message (^...$) so a string-content mutation is KILLED, not
    # merely matched as a substring (mutation-discipline, CLAUDE.md §3.6).
    with pytest.raises(
        QuorumNotReached, match=r"^top answer has 1 vote\(s\); quorum 2 not reached$"
    ):
        reconcile_exact_majority(("A", "B", "C"), quorum=2)


@pytest.mark.unit
def test_empty_answers_refused() -> None:
    # exact, anchored message -> a wrapped/edited string literal mutant is killed.
    with pytest.raises(QuorumNotReached, match=r"^no answers to reconcile$"):
        reconcile_exact_majority((), quorum=1)


@pytest.mark.unit
def test_non_positive_quorum_refused() -> None:
    # exact, anchored message -> kills a string-literal mutation on the raise.
    with pytest.raises(ValueError, match=r"^quorum must be a positive integer$"):
        reconcile_exact_majority(("A",), quorum=0)


# ------------------------------ free-text path ------------------------------ #


@pytest.mark.unit
def test_free_text_normalises_for_voting_but_returns_original() -> None:
    # Three phrasings that normalise equal (case + whitespace) reach quorum 2 and the
    # ORIGINAL text of the first supporter is returned (deterministic, replay-stable).
    answers = ("The  Answer", "the answer", "THE ANSWER")
    assert reconcile_free_text(answers, quorum=2) == "The  Answer"


@pytest.mark.unit
def test_free_text_whitespace_collapse_is_load_bearing() -> None:
    # Without the `split()`/join whitespace collapse these would be DISTINCT answers and
    # quorum 2 would fail. They must normalise to one group -> kills the split() mutant.
    answers = ("yes  please", "yes\tplease", "yes   please")
    assert reconcile_free_text(answers, quorum=2) == "yes  please"


@pytest.mark.unit
def test_free_text_join_separator_is_a_single_space_not_empty() -> None:
    # Normalisation collapses runs of whitespace to a SINGLE space (join sep " ").
    # "two words" and "twowords" must stay DISTINCT: if the join separator were
    # mutated to "" the words would run together and wrongly merge. With three votes
    # for the spaced form (quorum 3) and one for the joined form, the spaced form wins
    # and the joined singleton can never reach quorum -> proves the separator is " ".
    spaced = ("two   words", "two words", "TWO  WORDS")  # all normalise to "two words"
    assert reconcile_free_text(spaced, quorum=3) == "two   words"
    # control: the run-together form is a DIFFERENT group, so adding it does not change
    # the spaced group's quorum (it would, if the separator collapsed to "").
    mixed = ("two words", "two words", "twowords")
    with pytest.raises(QuorumNotReached):
        reconcile_free_text(mixed, quorum=3)  # only 2 of "two words"; not 3


@pytest.mark.unit
def test_free_text_maps_each_normalised_form_to_its_own_first_original() -> None:
    # zip(answers, normalised) pairs each ORIGINAL with ITS normalised form. A swap or
    # mis-pairing would return the wrong original. Two distinct groups, each with its
    # own winner depending on quorum, prove the mapping is answer->its-own-normal.
    answers = ("Alpha One", "alpha one", "Beta Two", "beta two", "ALPHA ONE")
    # "alpha one" group has 3 votes (indices 0,1,4); quorum 3 -> winner = first
    # original of THAT group, "Alpha One" (index 0), not a Beta original.
    assert reconcile_free_text(answers, quorum=3) == "Alpha One"


@pytest.mark.unit
def test_free_text_case_fold_is_load_bearing() -> None:
    # Without casefold() these differ only by case and would be distinct -> quorum unmet.
    # With it they are one group; kills the casefold() mutant.
    with pytest.raises(QuorumNotReached):
        # control: if case mattered, "YES"/"yes"/"Yes" are 3 distinct singletons.
        reconcile_exact_majority(("YES", "yes", "Yes"), quorum=2)
    assert reconcile_free_text(("YES", "yes", "Yes"), quorum=2) == "YES"


@pytest.mark.unit
def test_free_text_returns_first_input_original_not_a_later_one() -> None:
    # The winning group's returned text must be the FIRST input member's original (the
    # zip first-occurrence mapping), not a later phrasing -> kills a mutant that picks
    # a different representative.
    answers = ("First Form", "first form", "FIRST  FORM")  # all normalise equal
    assert reconcile_free_text(answers, quorum=3) == "First Form"


@pytest.mark.property
@given(
    base=st.sampled_from(["yes", "no", "maybe"]),
    pad=st.integers(min_value=1, max_value=4),
)
def test_free_text_majority_is_normalisation_invariant(base: str, pad: int) -> None:
    # The same answer with varied whitespace/case is one vote group; a clear majority
    # of it is returned regardless of phrasing noise.
    noisy = tuple([f"  {base.upper()} "] + [base] * (pad + 1))
    quorum = pad + 1
    assert reconcile_free_text(noisy, quorum).strip().casefold() == base


@pytest.mark.unit
def test_free_text_empty_refused() -> None:
    # anchored exact message kills the free-text path's empty-guard string mutant.
    with pytest.raises(QuorumNotReached, match=r"^no answers to reconcile$"):
        reconcile_free_text((), quorum=1)
