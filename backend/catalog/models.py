from django.db import models


class Corridor(models.Model):
    class Phase(models.TextChoices):
        UNDER_CONSTRUCTION = "under_construction", "Under construction"
        APPROVED = "approved", "Approved"
        PROPOSED = "proposed", "Proposed / study"

    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=80, blank=True)
    length_km = models.PositiveSmallIntegerField(null=True, blank=True)
    phase = models.CharField(
        max_length=32,
        choices=Phase.choices,
        default=Phase.PROPOSED,
        db_index=True,
    )
    status = models.CharField(
        max_length=255,
        blank=True,
        help_text="Public status line for the site / API.",
    )

    class Meta:
        ordering = ["slug"]

    def __str__(self) -> str:
        return self.name


class Station(models.Model):
    corridor = models.ForeignKey(Corridor, on_delete=models.CASCADE, related_name="stations")
    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    state_code = models.CharField(max_length=2)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_live = models.BooleanField(
        default=False,
        help_text="True when this stop is on the first expected commercial stretch.",
    )
    explore_lead = models.TextField(
        blank=True,
        help_text="Intro copy for the station explore / nearby panel.",
    )

    class Meta:
        ordering = ["corridor", "sort_order", "slug"]
        indexes = [models.Index(fields=["corridor", "sort_order"])]

    def __str__(self) -> str:
        return self.name