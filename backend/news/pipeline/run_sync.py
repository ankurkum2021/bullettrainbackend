"""Shared news sync steps for cron, watcher, and bootstrap."""

from __future__ import annotations

from pathlib import Path

from django.core.management import call_command
from django.db.models import Count

from news.models import NewsArticle
from news.pipeline.sync import export_updates_json, import_updates_json, repo_root, sync_nhsrcl_press_feed

# Fewer than this published rows → merge repo data/updates.json once (deploy backfill).
BACKFILL_JSON_MAX_ARTICLES = 12


def run_news_sync(
    *,
    skip_nhsrcl: bool = False,
    backfill_json: bool = False,
    export_json: bool = False,
    updates_path: Path | None = None,
    reprocess: bool = True,
    prune: bool = True,
) -> dict:
    """
    Pull NHSRCL press listing, optionally seed from bundled JSON, rewrite copy, dedupe.
    Safe to run from cron every few minutes.
    """
    path = updates_path or (repo_root() / "data" / "updates.json")
    result: dict = {"backfill": None, "nhsrcl": None, "exported": 0}

    if backfill_json and path.is_file():
        published = NewsArticle.objects.filter(is_published=True).aggregate(n=Count("id"))["n"] or 0
        if published < BACKFILL_JSON_MAX_ARTICLES:
            result["backfill"] = import_updates_json(path)

    if not skip_nhsrcl:
        try:
            result["nhsrcl"] = sync_nhsrcl_press_feed()
        except RuntimeError as exc:
            result["nhsrcl_error"] = str(exc)

    if reprocess:
        call_command("reprocess_articles", verbosity=0)
    if prune:
        call_command("prune_duplicate_articles", verbosity=0)

    if export_json:
        result["exported"] = export_updates_json(path)

    return result