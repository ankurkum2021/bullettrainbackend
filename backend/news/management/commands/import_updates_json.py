import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date

from news.models import NewsArticle


class Command(BaseCommand):
    help = "Import articles from data/updates.json into NewsArticle rows."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            default="",
            help="Path to updates JSON (default: repo data/updates.json)",
        )

    def handle(self, *args, **options):
        raw_path = options["path"]
        if raw_path:
            path = Path(raw_path)
        else:
            path = Path(__file__).resolve().parents[4] / "data" / "updates.json"

        if not path.is_file():
            self.stderr.write(self.style.ERROR(f"File not found: {path}"))
            return

        payload = json.loads(path.read_text(encoding="utf-8"))
        created = updated = 0

        for row in payload:
            slug = row["id"]
            published = parse_date(row["date"])
            if not isinstance(published, date):
                raise ValueError(f"Bad date for {slug}: {row['date']!r}")

            obj, was_created = NewsArticle.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": row["title"],
                    "summary": row["summary"],
                    "published_on": published,
                    "source_url": row["sourceUrl"],
                    "source_name": row["sourceName"],
                    "is_published": True,
                    "source_fingerprint": slug,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Import done: {created} created, {updated} updated."))