import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Station
from places.models import Place, PlaceKind, PlaceSection


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


class Command(BaseCommand):
    help = "Import station places from data/places-realistic.json (or override --path)."

    def add_arguments(self, parser):
        parser.add_argument("--path", type=str, default="")

    @transaction.atomic
    def handle(self, *args, **options):
        repo = _repo_root()
        if options.get("path"):
            path = Path(options["path"])
        else:
            path = repo / "data" / "places-realistic.json"
            if not path.is_file():
                path = repo / "data" / "places-seed.json"
        if not path.is_file():
            self.stderr.write(self.style.ERROR(f"Missing {path}"))
            return

        payload = json.loads(path.read_text(encoding="utf-8"))
        kinds = {k.slug: k for k in PlaceKind.objects.all()}
        if not kinds:
            self.stderr.write(self.style.ERROR("Run seed_place_kinds first."))
            return

        sections_created = places_created = 0

        for station_slug, block in payload.get("stations", {}).items():
            try:
                station = Station.objects.get(slug=station_slug)
            except Station.DoesNotExist:
                self.stderr.write(self.style.WARNING(f"Skipping unknown station: {station_slug}"))
                continue

            if block.get("lead"):
                station.explore_lead = block["lead"]
                station.save(update_fields=["explore_lead"])

            section_by_slug: dict[str, PlaceSection] = {}
            for i, sec in enumerate(block.get("sections", [])):
                section, created = PlaceSection.objects.update_or_create(
                    station=station,
                    slug=sec["slug"],
                    defaults={
                        "label": sec["label"],
                        "icon": sec.get("icon", ""),
                        "panel_title": sec.get("panelTitle", ""),
                        "sort_order": i * 10,
                    },
                )
                section_by_slug[sec["slug"]] = section
                if created:
                    sections_created += 1

                for j, row in enumerate(sec.get("places", [])):
                    kind = kinds.get(row["kind"])
                    if not kind:
                        self.stderr.write(self.style.WARNING(f"Unknown kind {row['kind']!r} — skip {row['name']}"))
                        continue
                    _, created = Place.objects.update_or_create(
                        station=station,
                        slug=row["slug"],
                        defaults={
                            "kind": kind,
                            "section": section,
                            "name": row["name"],
                            "note": row.get("note", ""),
                            "distance_km": row.get("distanceKm"),
                            "external_url": row.get("externalUrl", row.get("href", "")),
                            "tags": row.get("tags", ""),
                            "sort_order": j * 10,
                            "is_published": True,
                        },
                    )
                    if created:
                        places_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import done: sections created~{sections_created}, places created~{places_created}"
            )
        )