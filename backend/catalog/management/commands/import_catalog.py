import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Corridor, Station


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _import_corridor_block(corridor_data: dict, stations: list) -> tuple[int, int]:
    length_km = corridor_data.get("lengthKm")
    corridor, _ = Corridor.objects.update_or_create(
        slug=corridor_data["slug"],
        defaults={
            "name": corridor_data["name"],
            "short_name": corridor_data.get("shortName", "") or "",
            "length_km": length_km if length_km is not None else None,
            "phase": corridor_data.get("phase", Corridor.Phase.PROPOSED),
            "status": corridor_data.get("status", "") or "",
        },
    )

    created = 0
    updated = 0
    for row in stations:
        _, was_created = Station.objects.update_or_create(
            slug=row["slug"],
            defaults={
                "corridor": corridor,
                "name": row["name"],
                "state_code": row["stateCode"],
                "sort_order": row["order"],
                "is_live": row.get("live", False),
            },
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return created, updated


class Command(BaseCommand):
    help = "Import corridors and stations from data/corridors-catalog.json (or legacy mahsr-catalog.json)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            help="Path to catalog JSON (default: <repo>/data/corridors-catalog.json)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        repo_root = _repo_root()
        json_path = (
            Path(options["path"])
            if options.get("path")
            else repo_root / "data" / "corridors-catalog.json"
        )
        if not json_path.is_file():
            legacy = repo_root / "data" / "mahsr-catalog.json"
            if legacy.is_file():
                json_path = legacy
            else:
                self.stderr.write(self.style.ERROR(f"Missing catalog file: {json_path}"))
                return

        payload = json.loads(json_path.read_text(encoding="utf-8"))

        total_created = 0
        total_updated = 0
        corridor_count = 0

        if "corridors" in payload:
            for block in payload["corridors"]:
                corridor_count += 1
                created, updated = _import_corridor_block(block, block.get("stations", []))
                total_created += created
                total_updated += updated
                self.stdout.write(
                    f"  {block['slug']}: stations created={created}, updated={updated}"
                )
        else:
            corridor_count = 1
            created, updated = _import_corridor_block(payload["corridor"], payload["stations"])
            total_created += created
            total_updated += updated
            self.stdout.write(
                f"  {payload['corridor']['slug']}: stations created={created}, updated={updated}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {corridor_count} corridor(s); "
                f"stations created={total_created}, updated={total_updated}"
            )
        )