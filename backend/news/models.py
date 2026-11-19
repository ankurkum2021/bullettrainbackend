from django.db import models


class NewsArticle(models.Model):
    """One official-source item shown on /updates and the home feed."""

    slug = models.SlugField(
        max_length=120,
        unique=True,
        help_text="Stable site id (used in /updates#slug).",
    )
    title = models.CharField(max_length=300)
    teaser = models.CharField(
        max_length=220,
        blank=True,
        help_text="Short line for home feed cards.",
    )
    summary = models.TextField()
    body = models.TextField(
        blank=True,
        help_text="Full on-site article text (SEO).",
    )
    published_on = models.DateField(db_index=True)
    source_url = models.URLField(max_length=500)
    source_name = models.CharField(max_length=120)
    is_published = models.BooleanField(default=True)
    related_station = models.ForeignKey(
        "catalog.Station",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="news_articles",
    )
    source_fingerprint = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text="Hash or id from fetch pipeline for deduplication.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_on", "-created_at"]
        indexes = [
            models.Index(fields=["-published_on", "is_published"]),
        ]

    def __str__(self) -> str:
        return self.title