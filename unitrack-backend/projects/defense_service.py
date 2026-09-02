import re
from collections import OrderedDict

from .feedback_themes import FEEDBACK_THEME_TAXONOMY, _themes_for_feedback
from .models import Project, Submission, SubmissionReview


CATEGORY_LABELS = OrderedDict(
    [
        ("headings", "Section structure"),
        ("objectives", "Research objective"),
        ("methods", "Methodology"),
        ("results", "Results or analysis"),
        ("literature", "Literature review"),
        ("feedback_weak_point", "Unresolved feedback"),
        ("revision_warning", "Revision warning"),
    ]
)

DIFFICULTY_LEVELS = ("easy", "medium", "hard")
HEADING_PATTERN = re.compile(
    r"(?im)^\s*(?:chapter\s+\w+|section\s+\w+|\d+\.\d+|#{1,3})\s*[:\-]?\s*(.+)$"
)
KEY_TERM_PATTERN = re.compile(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})\b")
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")
MAX_SEEDS_PER_SOURCE = 4
DEFAULT_LIMIT = 5
MIN_LIMIT = 1
MAX_LIMIT = 25


def _clip(text, max_chars=240):
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _split_sentences(text, limit=8):
    if not text:
        return []
    sentences = SENTENCE_PATTERN.split(text)
    return [sentence.strip() for sentence in sentences if sentence.strip()][:limit]


def _truncate(text, max_chars):
    return text[:max_chars] if text else ""


def _seed(category, difficulty, source_type, source_id, section, evidence, rationale, talking_points=None):
    seed = {
        "category": category,
        "difficulty": difficulty,
        "source_type": source_type,
        "source_id": source_id,
        "section": section,
        "evidence": _clip(evidence),
        "rationale": _clip(rationale, 180),
    }
    if talking_points:
        seed["expected_talking_points"] = [_clip(point, 120) for point in talking_points[:3]]
    return seed


def _seeds_from_chapter(submission):
    text = submission.extracted_text or ""
    if submission.extraction_status != "success" or not text.strip():
        return [], "extraction_unavailable"

    seeds = []
    section_label = submission.milestone.replace("_", " ").title()

    headings = list(HEADING_PATTERN.findall(text))
    sentences = _split_sentences(text)
    terms = list(KEY_TERM_PATTERN.findall(text))

    if headings:
        heading = headings[0].strip()
        seeds.append(
            _seed(
                category="headings",
                difficulty="easy",
                source_type="submission",
                source_id=submission.id,
                section=section_label,
                evidence=f"Section heading: {heading}",
                rationale="Asks the student to summarize a section they wrote.",
                talking_points=[heading],
            )
        )

    for sentence in sentences:
        lowered = sentence.lower()
        if "objective" in lowered:
            seeds.append(
                _seed(
                    category="objectives",
                    difficulty="medium",
                    source_type="submission",
                    source_id=submission.id,
                    section=section_label,
                    evidence=_truncate(sentence, 200),
                    rationale="Project objective statement from the student's own writing.",
                )
            )
        elif any(term in lowered for term in ("method", "sampling", "approach", "design")):
            seeds.append(
                _seed(
                    category="methods",
                    difficulty="medium",
                    source_type="submission",
                    source_id=submission.id,
                    section=section_label,
                    evidence=_truncate(sentence, 200),
                    rationale="Methodology sentence from the student's own writing.",
                )
            )
        elif any(term in lowered for term in ("result", "find", "analysis", "data show")):
            seeds.append(
                _seed(
                    category="results",
                    difficulty="hard",
                    source_type="submission",
                    source_id=submission.id,
                    section=section_label,
                    evidence=_truncate(sentence, 200),
                    rationale="Result/analysis sentence from the student's own writing.",
                )
            )

    for term in terms[:2]:
        seeds.append(
            _seed(
                category="literature",
                difficulty="easy",
                source_type="submission",
                source_id=submission.id,
                section=section_label,
                evidence=f"Key term: {term}",
                rationale="Asks the student to define a key term in their own work.",
            )
        )

    seeds = seeds[:MAX_SEEDS_PER_SOURCE]
    if headings and (not seeds or seeds[0].get("category") != "headings"):
        seeds.insert(
            0,
            _seed(
                category="headings",
                difficulty="easy",
                source_type="submission",
                source_id=submission.id,
                section=section_label,
                evidence=f"Section heading: {headings[0].strip()}",
                rationale="Asks the student to summarize a section they wrote.",
                talking_points=[headings[0].strip()],
            ),
        )
    seeds = seeds[:MAX_SEEDS_PER_SOURCE]
    return seeds, None


def _seeds_from_reviews(student, project):
    seeds = []
    seen = set()
    reviews = SubmissionReview.objects.filter(
        submission__project=project, submission__project__student=student
    ).select_related("submission")

    for review in reviews:
        themes = _themes_for_feedback(review.feedback)
        if not themes:
            continue
        for theme in themes:
            key = (theme, review.id)
            if key in seen:
                continue
            seen.add(key)
            seeds.append(
                _seed(
                    category="feedback_weak_point",
                    difficulty="hard",
                    source_type="review",
                    source_id=review.id,
                    section=review.submission.milestone.replace("_", " ").title(),
                    evidence=_clip(review.feedback),
                    rationale=f"Prior reviewer flagged a {theme.replace('_', ' ')} issue; the student must address it.",
                )
            )
            if len(seeds) >= MAX_SEEDS_PER_SOURCE:
                return seeds
    return seeds


def _revision_warning_seeds(project):
    if project.status != "proposal_pending":
        return []
    return [
        _seed(
            category="revision_warning",
            difficulty="easy",
            source_type="project",
            source_id=project.id,
            section="Project status",
            evidence="Project proposal is still pending review.",
            rationale="Supervisor has not yet approved the proposal.",
            talking_points=["Proposal status", "Next milestone"],
        )
    ]


def build_defense_seeds(student, *, milestone=None, category=None, difficulty=None, limit=DEFAULT_LIMIT):
    limit = max(MIN_LIMIT, min(int(limit), MAX_LIMIT))
    project = (
        Project.objects.filter(student=student)
        .select_related("supervisor")
        .order_by("-created_at")
        .first()
    )
    warnings = []
    seeds = []

    if project is None:
        warnings.append("no_project")
        return {
            "seeds": [],
            "warnings": warnings,
            "available_categories": list(CATEGORY_LABELS.keys()),
            "available_difficulties": list(DIFFICULTY_LEVELS),
        }

    submissions = Submission.objects.filter(
        project=project,
        extraction_status="success",
    )
    if milestone:
        submissions = submissions.filter(milestone=milestone)
    submissions = submissions.order_by("-version")

    if not submissions.exists():
        warnings.append("insufficient_approved_chapter")
    else:
        for submission in submissions:
            chapter_seeds, warning = _seeds_from_chapter(submission)
            if warning:
                warnings.append(warning)
            seeds.extend(chapter_seeds)

    seeds.extend(_seeds_from_reviews(student, project))
    seeds.extend(_revision_warning_seeds(project))

    if category:
        seeds = [seed for seed in seeds if seed["category"] == category]
    if difficulty:
        seeds = [seed for seed in seeds if seed["difficulty"] == difficulty]

    seen = set()
    unique = []
    for seed in seeds:
        key = (seed["category"], seed["source_type"], seed["source_id"], seed["evidence"].lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(seed)

    return {
        "seeds": unique[:limit],
        "warnings": warnings,
        "available_categories": list(CATEGORY_LABELS.keys()),
        "available_difficulties": list(DIFFICULTY_LEVELS),
    }