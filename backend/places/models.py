from django.db import models


class PlaceKind(models.Model):
    """Generic taxonomy for local listings (transport, lodging, industry, etc.)."""

    slug = models.SlugField(max_length=48, unique=True)
    label = models.CharField(max_length=80)
    description = models.CharField(max_length=255, blank=True)
    icon = models.CharField(
        max_length=32,
        blank=True,
        help_text="Optional icon key for the front-end (e.g. cab, hotel, pin).",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "slug"]

    def __str__(self) -> str:
        return self.label


class PlaceSection(models.Model):
    """
    Optional UI grouping per station (e.g. 'Diamond belt', 'Airport transfers').
    Places can roll up under a section independent of kind.
    """

    station = models.ForeignKey(
        "catalog.Station",
        on_delete=models.CASCADE,
        related_name="place_sections",
    )
    slug = models.SlugField(max_length=64)
    label = models.CharField(max_length=120)
    icon = models.CharField(max_length=32, blank=True)
    panel_title = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["station", "sort_order", "slug"]
        unique_together = [("station", "slug")]

    def __str__(self) -> str:
        return f"{self.station.slug}:{self.label}"


class Place(models.Model):
    """A local listing or point of interest near a bullet train stop."""

    station = models.ForeignKey(
        "catalog.Station",
        on_delete=models.CASCADE,
        related_name="places",
    )
    kind = models.ForeignKey(
        PlaceKind,
        on_delete=models.PROTECT,
        related_name="places",
    )
    section = models.ForeignKey(
        PlaceSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="places",
    )
    slug = models.SlugField(max_length=80)
    name = models.CharField(max_length=200)
    note = models.TextField(blank=True)
    distance_km = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Illustrative road distance from the station — not routing API.",
    )
    external_url = models.URLField(max_length=500, blank=True)
    tags = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated facets (e.g. gst-invoice,b2b,airport).",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["station", "sort_order", "name"]
        unique_together = [("station", "slug")]
        indexes = [
            models.Index(fields=["station", "kind", "is_published"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def tag_list(self) -> list[str]:
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]