from __future__ import annotations

import re

from news.models import NewsArticle
from news.pipeline.rewrite import clean_headline


def _normalize_title(title: str) -> str:
    t = clean_headline(title).lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def is_duplicate_story(title: str, published_on) -> bool:
    """Skip NHSRCL auto-ingest when a curated row already covers the same story."""
    norm = _normalize_title(title)
    if not norm:
        return False

    qs = NewsArticle.objects.filter(published_on=published_on, is_published=True)
    for existing in qs:
        en = _normalize_title(existing.title)
        if not en:
            continue
        if norm == en or norm in en or en in norm:
            return True
        # Same-week energisation / OHE dupes
        if "energis" in norm and "energis" in en and "surat" in norm and "surat" in en:
            return True
    return False