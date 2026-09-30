"""AD-5: what of the model's answer may be shown. Pure.

The model is asked to cite every sentence, and sometimes does not. NFR-8 needs
zero uncited sentences, so the server checks rather than trusts: a sentence
with no source, or a source outside the records it was given, is dropped.
"""

from dataclasses import dataclass

from app.domains.search.constants import ANSWER_SENTENCE_LIMIT
from app.domains.search.interfaces.dtos import AnswerDraftDTO, AnswerSentenceDTO


@dataclass(frozen=True)
class CheckedAnswer:
    """Sentences cite 1 to n, numbered by first use. ``cited_numbers[i]`` is
    the prompt's record number that citation ``i + 1`` stands for."""

    sentences: list[AnswerSentenceDTO]
    cited_numbers: list[int]


def check_answer(*, draft: AnswerDraftDTO, record_count: int) -> CheckedAnswer | None:
    """The showable answer, or None when nothing survives (FR-18).

    In order: drop a sentence with no sources or any source outside 1 to
    ``record_count``; keep the first four; renumber citations by first use.
    """
    if not draft.supported:
        return None
    kept = [
        (text.strip(), sources)
        for text, sources in draft.sentences
        if text.strip()
        and sources
        and all(1 <= source <= record_count for source in sources)
    ][:ANSWER_SENTENCE_LIMIT]
    if not kept:
        return None

    cited_numbers: list[int] = []
    sentences: list[AnswerSentenceDTO] = []
    for text, sources in kept:
        citations: list[int] = []
        for source in sources:
            if source not in cited_numbers:
                cited_numbers.append(source)
            citation = cited_numbers.index(source) + 1
            if citation not in citations:
                citations.append(citation)
        sentences.append(AnswerSentenceDTO(text=text, citations=citations))
    return CheckedAnswer(sentences=sentences, cited_numbers=cited_numbers)
