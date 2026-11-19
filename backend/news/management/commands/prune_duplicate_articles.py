from django.core.management.base import BaseCommand
from django.db import transaction

from news.models import NewsArticle
from news.pipeline.dedupe import _normalize_title


class Command(BaseCommand):
    help = "Unpublish auto-ingested NHSRCL rows that duplicate a curated story on the same date."

    @transaction.atomic
    def handle(self, *args, **options):
        pruned = 0
        kept = NewsArticle.objects.filter(is_published=True).order_by("-published_on")
        by_date: dict = {}
        for article in kept:
            by_date.setdefault(article.published_on, []).append(article)

        for day, rows in by_date.items():
            norms = {_normalize_title(r.title): r for r in rows}
            for article in rows:
                norm = _normalize_title(article.title)
                if not norm:
                    continue
                if article.slug.startswith("media-brief"):
                    for other_norm, other in norms.items():
                        if other.id == article.id:
                            continue
                        if norm == other_norm or (norm in other_norm or other_norm in norm):
                            article.is_published = False
                            article.save(update_fields=["is_published"])
                            pruned += 1
                            self.stdout.write(f"Unpublished duplicate: {article.slug}")
                            break

        # Cross-date topic dupes (e.g. curated OHE story + later media-brief headline)
        topic_keys = ("energis", "ohe", "traction substation", "trainset", "train set")
        for key in topic_keys:
            group = [
                a
                for a in NewsArticle.objects.filter(is_published=True)
                if key in _normalize_title(a.title)
            ]
            if len(group) < 2:
                continue
            group.sort(
                key=lambda a: (
                    a.slug.startswith("media-brief"),
                    a.slug.startswith("media-brief-first"),
                    -a.published_on.toordinal(),
                )
            )
            keeper = group[0]
            for dup in group[1:]:
                dup.is_published = False
                dup.save(update_fields=["is_published"])
                pruned += 1
                self.stdout.write(
                    f"Unpublished topic duplicate {dup.slug} (kept {keeper.slug})"
                )

        self.stdout.write(self.style.SUCCESS(f"Pruned {pruned} duplicate(s)."))