from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand

from news.pipeline.sync import export_updates_json, import_updates_json, repo_root, sync_nhsrcl_press_feed


class Command(BaseCommand):
    help = (
        "Seed corridor/stations, import curated data/updates.json, "
        "merge the live NHSRCL press feed, and optionally refresh data/updates.json."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-catalog",
            action="store_true",
            help="Do not run import_catalog.",
        )
        parser.add_argument(
            "--skip-json",
            action="store_true",
            help="Do not import data/updates.json.",
        )
        parser.add_argument(
            "--skip-nhsrcl",
            action="store_true",
            help="Do not fetch the NHSRCL press listing.",
        )
        parser.add_argument(
            "--export-json",
            action="store_true",
            help="Write merged articles back to data/updates.json (Next.js fallback file).",
        )
        parser.add_argument(
            "--updates-path",
            type=str,
            default="",
            help="Override path to updates JSON.",
        )

    def handle(self, *args, **options):
        if not options["skip_catalog"]:
            self.stdout.write("Importing corridors + stations …")
            call_command("import_catalog")

        updates_path = Path(options["updates_path"]) if options["updates_path"] else repo_root() / "data" / "updates.json"

        if not options["skip_json"]:
            if not updates_path.is_file():
                self.stderr.write(self.style.WARNING(f"Skipping JSON import — not found: {updates_path}"))
            else:
                stats = import_updates_json(updates_path)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"updates.json: {stats['rows']} rows ({stats['created']} created, {stats['updated']} updated)"
                    )
                )

        if not options["skip_nhsrcl"]:
            try:
                stats = sync_nhsrcl_press_feed()
                self.stdout.write(
                    self.style.SUCCESS(
                        "NHSRCL feed: "
                        f"{stats['fetched']} listed, {stats['created']} new, "
                        f"{stats['updated']} updated, {stats['skipped']} unchanged"
                    )
                )
            except RuntimeError as exc:
                self.stderr.write(self.style.ERROR(str(exc)))

        if options["export_json"]:
            count = export_updates_json(updates_path)
            self.stdout.write(self.style.SUCCESS(f"Exported {count} articles → {updates_path}"))