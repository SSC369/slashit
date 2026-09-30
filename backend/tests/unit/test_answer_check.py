"""Epic 005, sub-plan 4.2, C-2.2 to C-2.4: AD-5's check on the model's answer
(FR-17, FR-18)."""

from app.domains.search.interfaces.dtos import AnswerDraftDTO
from app.domains.search.services.answer_check import CheckedAnswer, check_answer


def _check(
    sentences: list[tuple[str, list[int]]], *, supported: bool = True, count: int = 3
) -> CheckedAnswer | None:
    return check_answer(
        draft=AnswerDraftDTO(sentences=sentences, supported=supported),
        record_count=count,
    )


def test_an_uncited_sentence_is_dropped() -> None:
    """C-2.2, NFR-8: zero uncited sentences reach the user."""
    checked = _check([("Your passport expires in 2030.", [2]), ("Also, relax.", [])])

    assert checked is not None
    assert [sentence.text for sentence in checked.sentences] == [
        "Your passport expires in 2030."
    ]


def test_a_sentence_citing_a_record_it_was_not_given_is_dropped() -> None:
    """C-2.2: record 11 does not exist among three."""
    checked = _check([("Made up.", [11]), ("Real.", [1]), ("Half real.", [1, 4])])

    assert checked is not None
    assert [sentence.text for sentence in checked.sentences] == ["Real."]


def test_at_most_four_sentences_are_kept() -> None:
    """C-2.2, FR-16."""
    checked = _check([(f"Sentence {index}.", [1]) for index in range(6)])

    assert checked is not None
    assert len(checked.sentences) == 4


def test_nothing_valid_means_no_support() -> None:
    """C-2.3, FR-18."""
    assert _check([("Uncited.", [])]) is None
    assert _check([]) is None


def test_an_unsupported_answer_shows_nothing_even_if_it_cites() -> None:
    """C-2.3: the model said the records do not answer; nothing is shown."""
    assert _check([("Guess.", [1])], supported=False) is None


def test_citations_are_renumbered_by_first_use() -> None:
    """C-2.4: markers always read [1], [2] top down."""
    checked = _check([("A.", [3]), ("B.", [1, 3]), ("C.", [2])])

    assert checked is not None
    assert [sentence.citations for sentence in checked.sentences] == [[1], [2, 1], [3]]
    assert checked.cited_numbers == [3, 1, 2]
