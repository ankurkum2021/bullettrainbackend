from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

from django.db import transaction

from catalog.models import Station
from news.models import NewsArticle
from news.pipeline.dedupe import is_duplicate_story
from news.pipeline.nhsrcl import fetch_latest_press_releases
from news.pipeline.rewrite import rewrite_article_fields
from news.pipeline.stations import guess_related_station

SOURCE_NAME_NHSRCL = "NHSRCL press release"


def fingerprint_for_url(source_url: str) -> str:
    return hashlib.sha256(source_url.strip().encode("utf-8")).hexdigest()


def slug_from_source_url(source_url: str) -> str:
    slug = source_url.rstrip("/").split("/")[-1]
    return slug[:120] if slug else "article"


@transaction.atomic
def upsert_news_article(
    *,
    slug: str,
    title: str,
    summary: str,
    published_on: date,
    source_url: str,
    source_name: str,
    fingerprint: str | None = None,
    related_station: Station | None = None,
    teaser: str = "",
    body: str = "",
) -> tuple[NewsArticle, bool]:
    fp = fingerprint or fingerprint_for_url(source_url)
    if related_station is None:
        related_station = guess_related_station(title, summary)

    defaults = {
        "title": title,
        "summary": summary,
        "published_on": published_on,
        "source_url": source_url,
        "source_name": source_name,
        "is_published": True,
        "source_fingerprint": fp,
        "related_station": related_station,
    }
    if teaser:
        defaults["teaser"] = teaser
    if body:
        defaults["body"] = body

    obj, was_created = NewsArticle.objects.update_or_create(
        slug=slug,
        defaults=defaults,
    )
    return obj, was_created


def sync_nhsrcl_press_feed(*, enrich_summary: bool = False) -> dict[str, int]:
    """Pull the public press listing (first page) and upsert unseen releases."""
    del enrich_summary  # reserved for future HTML detail fetch
    items = fetch_latest_press_releases()
    created = updated = skipped = 0

    for item in items:
        fp = fingerprint_for_url(item.source_url)
        if NewsArticle.objects.filter(source_fingerprint=fp).exists():
            skipped += 1
            continue
        if is_duplicate_story(item.title, item.published_on):
            skipped += 1
            continue

        slug = slug_from_source_url(item.source_url)
        if NewsArticle.objects.filter(slug=slug).exclude(source_fingerprint=fp).exists():
            slug = f"{slug}-{item.published_on.isoformat()}"

        fields = rewrite_article_fields(
            title=item.title,
            summary="",
            published_on=item.published_on,
            source_name=SOURCE_NAME_NHSRCL,
        )

        _, was_created = upsert_news_article(
            slug=slug,
            title=fields["title"],
            teaser=fields["teaser"],
            summary=fields["summary"],
            body=fields["body"],
            published_on=item.published_on,
            source_url=item.source_url,
            source_name=fields["source_name"],
            fingerprint=fp,
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return {"fetched": len(items), "created": created, "updated": updated, "skipped": skipped}


def import_updates_json(path: Path) -> dict[str, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    created = updated = 0

    for row in payload:
        published_raw = row["date"]
        published = date.fromisoformat(published_raw)
        slug = row["id"]
        fp = row.get("sourceFingerprint") or fingerprint_for_url(row["sourceUrl"])
        station: Station | None = None
        station_slug = row.get("stationSlug")
        if station_slug:
            station = Station.objects.filter(slug=station_slug).first()

        fields = rewrite_article_fields(
            title=row["title"],
            summary=row["summary"],
            published_on=published,
            source_name=row["sourceName"],
        )
        _, was_created = upsert_news_article(
            slug=slug,
            title=fields["title"],
            teaser=fields["teaser"],
            summary=fields["summary"],
            body=fields["body"],
            published_on=published,
            source_url=row["sourceUrl"],
            source_name=fields["source_name"],
            fingerprint=fp,
            related_station=station,
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return {"rows": len(payload), "created": created, "updated": updated}


def export_updates_json(path: Path, *, limit: int = 100) -> int:
    rows = []
    qs = NewsArticle.objects.filter(is_published=True).select_related("related_station").order_by(
        "-published_on", "-created_at"
    )[:limit]

    for article in qs:
        row = {
            "id": article.slug,
            "title": article.title,
            "date": article.published_on.isoformat(),
            "summary": article.summary,
            "sourceUrl": article.source_url,
            "sourceName": article.source_name,
        }
        if article.related_station_id:
            row["stationSlug"] = article.related_station.slug
        rows.append(row)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(rows)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]