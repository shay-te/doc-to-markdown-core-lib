"""Picks the best candidate markdown from a list of extractor outputs.

The selection job is its own service so the orchestrator (which knows
*which* extractors to run for a file type) is separated from the
voting/agreement policy (which decides *which output* wins). Both are
intentionally stateless.
"""
import json
import re
from dataclasses import asdict
from typing import List, Optional

from core_lib.data_layers.service.service import Service

from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_report import (
    ExtractionReport,
)
from doc_to_markdown_core_lib.data_layers.data.extraction.flagged_region import (
    FlaggedRegion,
)
from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_result import (
    ExtractionResult,
)
from doc_to_markdown_core_lib.data_layers.data.tier import Tier


_UNCERTAIN_RE = re.compile(
    r'⚠️\[UNCERTAIN:\s*(?P<best>[^|\]]*?)\s*'
    r'(?:\|\s*candidates:\s*(?P<cands>[^\]]*?))?\s*\]'
)

_COMPLETENESS_TOKEN_FLOOR = 0.6

# Synthetic winner assembled page-by-page from the real candidates.
MERGE_EXTRACTOR_NAME = 'per_page_merge'
_PAGE_MARKER_RE = re.compile(r'<!-- page (\d+) -->')


class CandidateSelectionService(Service):
    """Stateless: picks the highest-confidence candidate, then
    cross-checks against the others (Jaccard agreement, token
    survival, inline UNCERTAIN flags) to compute the final
    ``overall_confidence`` and ``needs_review`` verdict.
    """

    def __init__(self, confidence_threshold: float = 0.8):
        self._confidence_threshold = confidence_threshold

    def select(
        self,
        candidates: List[ExtractionCandidate],
        *,
        tier: Tier,
        used: List[str],
        skipped: List[dict],
        filename: Optional[str],
    ) -> ExtractionResult:
        if not candidates:
            return self._build_empty_result(tier, used, skipped, filename)

        # Maximum accuracy: synthesize a per-page best-of across the
        # page-marked candidates and let it compete in the vote. Each page is
        # the version the ensemble corroborates most (text for text pages, OCR
        # for image-only pages), so the merge is normally the winner.
        pool = list(candidates)
        merged = _merge_pages(candidates)
        if merged is not None:
            pool.append(merged)

        # Highest confidence wins; but confidence saturates at 1.0 for any
        # real multi-page doc, so ties break toward the most *corroborated*
        # output — the candidate sharing the most tokens with its peers. A
        # noisy OCR that agrees with no one can't win on lineup order.
        winner = max(
            pool,
            key=lambda candidate: (
                candidate.confidence or 0.0,
                _corroborated_size(
                    candidate,
                    [other for other in pool if other is not candidate],
                ),
            ),
        )
        chosen_markdown = winner.markdown
        base_confidence = winner.confidence or 0.0
        winning_extractor = winner.extractor

        agreement = _agreement(candidates)
        overall_confidence = max(0.0, min(1.0, (base_confidence + agreement) / 2))

        chosen_markdown = _strip_bom(chosen_markdown)
        markdown_bytes = chosen_markdown.encode('utf-8')
        _assert_utf8(markdown_bytes)

        flagged_regions = _parse_flagged_regions(chosen_markdown)
        languages = _union_languages(candidates)
        completeness_ok = _completeness_ok(
            chosen_markdown, candidates, floor=_COMPLETENESS_TOKEN_FLOOR
        )

        if not completeness_ok:
            # The full candidate markdowns already live on the result's
            # ``candidates``; don't duplicate whole documents into the report.
            flagged_regions.append(
                FlaggedRegion(
                    location='document-tail',
                    best_guess='',
                    reason='chosen output is missing consensus content',
                )
            )
            chosen_markdown = chosen_markdown + (
                '\n\n⚠️[UNCERTAIN: extraction may be incomplete — see extraction_report.json]'
            )
            markdown_bytes = chosen_markdown.encode('utf-8')
            _assert_utf8(markdown_bytes)

        needs_review = (
            overall_confidence < self._confidence_threshold
            or bool(flagged_regions)
            or not completeness_ok
        )

        report = ExtractionReport(
            overall_confidence=round(overall_confidence, 4),
            tier=tier,
            extractors_used=used,
            extractors_skipped=skipped,
            languages_detected=languages,
            flagged_regions=flagged_regions,
            completeness_check=completeness_ok,
            winning_extractor=winning_extractor,
            agreement_score=round(agreement, 4),
            needs_review=needs_review,
            source_filename=filename,
        )
        report_bytes = json.dumps(
            asdict(report), ensure_ascii=False, indent=2
        ).encode('utf-8')
        _assert_utf8(report_bytes)

        return ExtractionResult(
            markdown=chosen_markdown,
            markdown_bytes=markdown_bytes,
            report=report,
            report_bytes=report_bytes,
            candidates=candidates,
        )

    def _build_empty_result(
        self,
        tier: Tier,
        used: List[str],
        skipped: List[dict],
        filename: Optional[str],
    ) -> ExtractionResult:
        report = ExtractionReport(
            overall_confidence=0.0,
            tier=tier,
            extractors_used=used,
            extractors_skipped=skipped,
            languages_detected=[],
            flagged_regions=[
                FlaggedRegion(
                    location='document',
                    best_guess='',
                    candidates=[],
                    reason='no extractor produced output',
                )
            ],
            completeness_check=False,
            winning_extractor=None,
            agreement_score=0.0,
            needs_review=True,
            source_filename=filename,
        )
        markdown = '⚠️[UNCERTAIN: no extractor could read this document]'
        markdown_bytes = markdown.encode('utf-8')
        _assert_utf8(markdown_bytes)
        report_bytes = json.dumps(
            asdict(report), ensure_ascii=False, indent=2
        ).encode('utf-8')
        _assert_utf8(report_bytes)
        return ExtractionResult(
            markdown=markdown,
            markdown_bytes=markdown_bytes,
            report=report,
            report_bytes=report_bytes,
            candidates=[],
        )


# Whitespace splitting collapses to one token per line for space-less
# scripts (CJK, Thai), destroying overlap; tokenize those per character.
_RANGES = (
    r'\u3040-\u30ff'  # hiragana + katakana
    r'\u3400-\u9fff'  # CJK ext-A + unified ideographs
    r'\uac00-\ud7af'  # hangul
    r'\uf900-\ufaff'  # CJK compatibility ideographs
    r'\u0e00-\u0e7f'  # thai
)
_TOKEN_RE = re.compile(f'[{_RANGES}]|[^\\s{_RANGES}]+')


def _tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text or '')


def _corroborated_token_count(tokens: set, other_token_sets: List[set]) -> int:
    corroborated = set()
    for other in other_token_sets:
        corroborated |= tokens & other
    return len(corroborated)


def _corroborated_size(
    candidate: ExtractionCandidate, others: List[ExtractionCandidate]
) -> int:
    """How many of this candidate's tokens at least one other extractor also
    produced. Rewards *complete* output (covering more real content) while
    ignoring solo noise, so it breaks confidence ties toward the extraction
    the ensemble corroborates most."""
    return _corroborated_token_count(
        set(_tokenize(candidate.markdown)),
        [set(_tokenize(other.markdown)) for other in others],
    )


def _split_pages(markdown: str):
    """``{page_number: text}`` for a page-marked candidate, else ``None``
    (whole-doc-only extractor). The marker is the shared
    ``<!-- page N -->`` every paged extractor emits."""
    matches = list(_PAGE_MARKER_RE.finditer(markdown or ''))
    if not matches:
        return None
    pages = {}
    for index, match in enumerate(matches):
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(markdown)
        )
        pages[int(match.group(1))] = markdown[match.end():end].strip()
    return pages


def _best_page_version(versions: List[str]) -> str:
    """The version of one page the other versions corroborate most (ties →
    longer): text pages agree among text extractors, image pages among OCR."""
    if len(versions) == 1:
        return versions[0]
    token_sets = [set(_tokenize(version)) for version in versions]
    best_index = max(
        range(len(versions)),
        key=lambda index: (
            _corroborated_token_count(
                token_sets[index],
                [
                    token_sets[other]
                    for other in range(len(versions))
                    if other != index
                ],
            ),
            len(versions[index]),
        ),
    )
    return versions[best_index]


def _merge_pages(candidates: List[ExtractionCandidate]):
    """Best-of-pages: assemble each page from the extractor the ensemble
    corroborates most on that page. Returns a synthetic candidate, or
    ``None`` when fewer than two candidates carry page markers."""
    paged = [
        pages
        for pages in (_split_pages(candidate.markdown) for candidate in candidates)
        if pages
    ]
    if len(paged) < 2:
        return None
    page_numbers = sorted({number for pages in paged for number in pages})
    parts = []
    for number in page_numbers:
        versions = [pages[number] for pages in paged if number in pages]
        parts.append(f'<!-- page {number} -->\n\n{_best_page_version(versions)}')
    markdown = '\n\n'.join(parts).strip()
    # Best-of each page → at least as trustworthy as its best source. Inherit
    # the top confidence rather than deriving from length, which would
    # under-rate a short merged doc against its own inputs.
    confidence = max((candidate.confidence or 0.0) for candidate in candidates)
    return ExtractionCandidate(
        extractor=MERGE_EXTRACTOR_NAME,
        markdown=markdown,
        confidence=confidence,
        languages=_union_languages(candidates),
    )


def _agreement(candidates: List[ExtractionCandidate]) -> float:
    # One (or zero) candidate has nothing to disagree with → full agreement;
    # the score then rides on the winner's own confidence.
    if len(candidates) <= 1:
        return 1.0
    token_sets = [
        set(_tokenize(candidate.markdown)) for candidate in candidates
    ]
    pairs = 0
    total = 0.0
    for left_index in range(len(token_sets)):
        for right_index in range(left_index + 1, len(token_sets)):
            left, right = token_sets[left_index], token_sets[right_index]
            if not left and not right:
                continue
            union = len(left | right)
            inter = len(left & right)
            total += (inter / union) if union else 0.0
            pairs += 1
    return total / pairs if pairs else 1.0


def _union_languages(candidates: List[ExtractionCandidate]) -> List[str]:
    seen = []
    for candidate in candidates:
        for lang in candidate.languages or []:
            if lang and lang not in seen:
                seen.append(lang)
    return seen


def _completeness_ok(
    chosen: str, candidates: List[ExtractionCandidate], floor: float
) -> bool:
    """Did the winner silently truncate? Measured against the *consensus* —
    content at least two extractors produced — not against each candidate.
    Comparing to every candidate would let one engine's junk (OCR noise,
    headers/footers the clean winner dropped) flag the winner as incomplete.

    Needs **3+ extractors** to mean anything: the winner is itself one of
    the candidates, so with ≤2 it always covers the pairwise consensus
    (the consensus ⊆ winner) and truncation is undetectable here — that
    case is left to the agreement score, which still drops when the winner
    disagrees with the other candidate. Known limitation: consensus can't
    tell apart genuine content from boilerplate two engines both emit.
    """
    if not candidates:
        return False
    if len(candidates) < 3:
        return True
    consensus = _consensus_tokens(candidates)
    if not consensus:
        return True
    covered = len(set(_tokenize(chosen)) & consensus) / len(consensus)
    return covered >= floor


def _consensus_tokens(candidates: List[ExtractionCandidate]):
    counts = {}
    for candidate in candidates:
        for token in set(_tokenize(candidate.markdown)):
            counts[token] = counts.get(token, 0) + 1
    return {token for token, count in counts.items() if count >= 2}


def _parse_flagged_regions(text: str) -> List[FlaggedRegion]:
    regions = []
    for match in _UNCERTAIN_RE.finditer(text or ''):
        best = (match.group('best') or '').strip()
        cands_str = (match.group('cands') or '').strip()
        cands = (
            [
                candidate_text.strip()
                for candidate_text in cands_str.split('|')
                if candidate_text.strip()
            ]
            if cands_str
            else []
        )
        regions.append(
            FlaggedRegion(
                location=f'offset {match.start()}',
                best_guess=best,
                candidates=cands,
            )
        )
    return regions


def _strip_bom(text: str) -> str:
    if not text:
        return text
    return text.lstrip('﻿')


def _assert_utf8(payload: bytes) -> None:
    payload.decode('utf-8')
    if payload.startswith(b'\xef\xbb\xbf'):
        raise ValueError('output starts with a UTF-8 BOM; spec forbids it')
