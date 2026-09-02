import re
from collections import OrderedDict
from difflib import SequenceMatcher

from .feedback_themes import FEEDBACK_THEME_TAXONOMY, _themes_for_feedback

PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")
HEADING_SPLIT = re.compile(r"(?m)^\s*#+\s+")
WORD_SPLIT = re.compile(r"\s+")

EXTRACTION_AVAILABLE = "success"


def split_paragraphs(text):
    if not text:
        return []
    return [paragraph.strip() for paragraph in PARAGRAPH_SPLIT.split(text) if paragraph.strip()]


def normalize_text(text):
    if not text:
        return ""
    collapsed = HEADING_SPLIT.sub("\n", text)
    return re.sub(r"[ \t]+", " ", collapsed).strip()


def _word_count(text):
    return len(WORD_SPLIT.split(text)) if text else 0


def diff_paragraphs(before_text, after_text):
    before = split_paragraphs(before_text)
    after = split_paragraphs(after_text)
    matcher = SequenceMatcher(a=before, b=after, autojunk=False)
    additions = []
    removals = []
    replacements = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "insert":
            additions.extend(after[j1:j2])
        elif tag == "delete":
            removals.extend(before[i1:i2])
        elif tag == "replace":
            for before_chunk, after_chunk in zip(before[i1:i2], after[j1:j2]):
                replacements.append({"before": before_chunk, "after": after_chunk})
            additions.extend(after[j1 + len(before[i1:i2]):])
            removals.extend(before[i1 + len(after[j1:j2]):])
    return additions, removals, replacements


def _similarity_ratio(before_text, after_text):
    if not before_text and not after_text:
        return 1.0
    return SequenceMatcher(a=before_text, b=after_text, autojunk=False).ratio()


def compute_diff(before_text, after_text, *, max_excerpt_chars=240):
    normalized_before = normalize_text(before_text)
    normalized_after = normalize_text(after_text)
    additions, removals, replacements = diff_paragraphs(normalized_before, normalized_after)
    before_words = _word_count(normalized_before)
    after_words = _word_count(normalized_after)
    similarity = round(_similarity_ratio(normalized_before, normalized_after) * 100, 2)

    def _clip(line):
        return line[:max_excerpt_chars]

    return {
        "word_count_before": before_words,
        "word_count_after": after_words,
        "word_count_delta": after_words - before_words,
        "similarity_percent": similarity,
        "change_ratio": round(100 - similarity, 2),
        "added_paragraphs": [_clip(line) for line in additions[:5]],
        "removed_paragraphs": [_clip(line) for line in removals[:5]],
        "replaced_paragraphs": [
            {"before": _clip(item["before"]), "after": _clip(item["after"])}
            for item in replacements[:5]
        ],
        "added_paragraph_total": len(additions),
        "removed_paragraph_total": len(removals),
        "replaced_paragraph_total": len(replacements),
    }


COVERAGE_RULES = OrderedDict(
    [
        ("likely_addressed", 0.6),
        ("possibly_addressed", 0.25),
    ]
)


def _evidence_for_theme(theme, before_text, after_text):
    phrases = FEEDBACK_THEME_TAXONOMY[theme]
    after_normalized = normalize_text(after_text).lower()
    matched_phrase = next(
        (phrase for phrase in phrases if phrase in after_normalized), None
    )
    return matched_phrase


def evaluate_feedback_coverage(reviews, after_text, *, max_evidence=3):
    if not reviews:
        return [], ["Heuristic: supervisor must verify each item below."]
    evidence = []
    for review in reviews:
        matched = _themes_for_feedback(review.feedback)
        if not matched:
            continue
        theme = matched[0]
        phrase = _evidence_for_theme(theme, "", after_text)
        after_normalized = normalize_text(after_text).lower()
        ratio = sum(
            1 for word in normalize_text(review.feedback).lower().split() if word in after_normalized
        )
        denominator = max(len(normalize_text(review.feedback).split()), 1)
        coverage_ratio = ratio / denominator
        if coverage_ratio >= COVERAGE_RULES["likely_addressed"]:
            status = "likely_addressed"
        elif coverage_ratio >= COVERAGE_RULES["possibly_addressed"]:
            status = "possibly_addressed"
        else:
            status = "not_evident"
        evidence.append(
            {
                "review_id": review.id,
                "submission_id": review.submission_id,
                "theme": theme,
                "status": status,
                "matched_phrase": phrase,
                "coverage_ratio": round(coverage_ratio, 2),
                "excerpt": review.feedback[:200],
                "warning": "Heuristic match; supervisor must verify.",
            }
        )
    evidence = evidence[:max_evidence]
    warnings = ["Heuristic: supervisor must verify whether feedback is substantively resolved."]
    if any(item["status"] == "not_evident" for item in evidence):
        warnings.append(
            "One or more review items show no evidence of being addressed in the new text."
        )
    return evidence, warnings