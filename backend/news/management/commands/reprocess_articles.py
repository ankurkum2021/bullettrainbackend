from django.core.management.base import BaseCommand
from django.db import transaction

from news.models import NewsArticle
from news.pipeline.rewrite import _is_generic_summary, rewrite_article_fields


class Command(BaseCommand):
    help = "Rewrite teasers, summaries, and on-site bodies for all published articles."

    def add_arguments(self, parser):
        parser.add_argument(
            "--only-generic",
            action="store_true",
            help="Only rows with placeholder NHSRCL sync summaries.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        qs = NewsArticle.objects.filter(is_published=True)
        updated = 0
        for article in qs:
            if options["only_generic"] and not _is_generic_summary(article.summary):
                if article.body and article.teaser:
                    continue
            fields = rewrite_article_fields(
                title=article.title,
                summary=article.summary,
                published_on=article.published_on,
                source_name=article.source_name,
            )
            article.title = fields["title"]
            article.teaser = fields["teaser"]
            article.summary = fields["summary"]
            article.body = fields["body"]
            article.source_name = fields["source_name"]
            article.save()
            updated += 1
        self.stdout.write(self.style.SUCCESS(f"Rewrote {updated} article(s)."))