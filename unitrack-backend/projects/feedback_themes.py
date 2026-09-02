import re
from collections import OrderedDict

from django.db.models import QuerySet

from .models import ProjectSession, SubmissionReview


FEEDBACK_THEME_TAXONOMY = OrderedDict(
    [
        ("citation_formatting", ("citation", "references", "formatting", "apa style")),
        ("methodology", ("methodology", "method", "research design", "sampling")),
        ("clarity", ("clarity", "clear", "ambiguous", "explain")),
        ("literature_review", ("literature", "related work", "sources", "theoretical framework")),
        ("analysis", ("analysis", "data", "results", "discussion")),
        ("structure", ("structure", "organization", "chapter", "section", "coherent")),
        ("grammar", ("grammar", "spelling", "punctuation", "sentence", "proofread")),
    ]
)


def normalize_feedback(text):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", text.lower())).strip()


def _themes_for_feedback(feedback):
    normalized = normalize_feedback(feedback)
    if not normalized:
        return []
    matches = []
    for theme, phrases in FEEDBACK_THEME_TAXONOMY.items():
        if any(re.search(rf"\b{re.escape(phrase)}\b", normalized) for phrase in phrases):
            matches.append(theme)
    return matches


def analyze_feedback_themes(
    reviews: QuerySet,
    *,
    min_occurrences=2,
    limit=5,
    evidence_limit=3,
):
    min_occurrences = max(1, min(int(min_occurrences), 100))
    limit = min(max(int(limit), 1), len(FEEDBACK_THEME_TAXONOMY))
    evidence_limit = min(max(int(evidence_limit), 1), 10)
    grouped = {key: [] for key in FEEDBACK_THEME_TAXONOMY}
    valid_reviews = reviews.exclude(feedback="").select_related(
        "submission__project__student", "reviewer"
    )

    for review in valid_reviews:
        matched_themes = _themes_for_feedback(review.feedback)
        for theme in matched_themes:
            grouped[theme].append(review)

    total_reviews = len(valid_reviews)
    themes = []
    for theme, theme_reviews in grouped.items():
        if len(theme_reviews) < min_occurrences:
            continue
        evidence = []
        for review in theme_reviews[:evidence_limit]:
            evidence.append(
                {
                    "review_id": review.id,
                    "submission_id": review.submission_id,
                    "student_id": review.submission.project.student_id,
                    "excerpt": normalize_feedback(review.feedback)[:240],
                }
            )
        themes.append(
            {
                "theme": theme,
                "label": theme.replace("_", " ").title(),
                "matched_review_count": len(theme_reviews),
                "distinct_submission_count": len({r.submission_id for r in theme_reviews}),
                "distinct_student_count": len({r.submission.project.student_id for r in theme_reviews}),
                "percentage": round((len(theme_reviews) / total_reviews) * 100, 2) if total_reviews else 0,
                "evidence": evidence,
            }
        )

    themes.sort(
        key=lambda item: (
            -item["matched_review_count"],
            -item["distinct_student_count"],
            item["theme"],
        )
    )
    return {
        "total_reviews": total_reviews,
        "total_submissions": len({r.submission_id for r in valid_reviews}),
        "total_students": len({r.submission.project.student_id for r in valid_reviews}),
        "themes": themes[:limit],
    }


def resolve_feedback_session(requested_session_id, default_session):
    if requested_session_id in (None, ""):
        return default_session
    return ProjectSession.objects.filter(pk=requested_session_id).first()
