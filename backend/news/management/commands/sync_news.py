from pathlib import Path

from django.core.management.base import BaseCommand

from news.pipeline.run_sync import run_news_sync
from news.pipeline.sync import repo_root


class Command(BaseCommand):
    help = (
        "Automated news pipeline: optional one-time JSON backfill, NHSRCL fetch, "
        "rewrite on-site copy, prune duplicates. Intended for cron/systemd."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-nhsrcl",
            action="store_true",
            help="Only reprocess/prune (or JSON backfill).",
        )
        parser.add_argument(
            "--backfill-json",
            action="store_true",
            help="Import data/updates.json when the DB has few articles (deploy seed).",
        )
        parser.add_argument(
            "--export-json",
            action="store_true",
            help="Write data/updates.json from DB (Next.js offline fallback).",
        )
        parser.add_argument("--updates-path", type=str, default="")
        parser.add_argument(
            "--no-reprocess",
            action="store_true",
            help="Skip rewrite pass (faster; not recommended in production).",
        )
        parser.add_argument(
            "--no-prune",
            action="store_true",
            help="Skip duplicate pruning.",
        )

    def handle(self, *args, **options):
        updates_path = (
            Path(options["updates_path"]) if options["updates_path"] else repo_root() / "data" / "updates.json"
        )

        result = run_news_sync(
            skip_nhsrcl=options["skip_nhsrcl"],
            backfill_json=options["backfill_json"],
            export_json=options["export_json"],
            updates_path=updates_path,
            reprocess=not options["no_reprocess"],
            prune=not options["no_prune"],
        )

        if result.get("backfill"):
            b = result["backfill"]
            self.stdout.write(
                self.style.SUCCESS(
                    f"Backfill JSON: {b['rows']} rows ({b['created']} new, {b['updated']} updated)"
                )
            )

        if result.get("nhsrcl_error"):
            self.stderr.write(self.style.ERROR(result["nhsrcl_error"]))
            if not result.get("backfill") and options["skip_nhsrcl"]:
                raise SystemExit(1)
        elif result.get("nhsrcl"):
            s = result["nhsrcl"]
            self.stdout.write(
                f"NHSRCL: listed {s['fetched']}, new {s['created']}, "
                f"updated {s['updated']}, skipped {s['skipped']}"
            )

        if options["export_json"] and result.get("exported"):
            self.stdout.write(
                self.style.SUCCESS(f"Exported {result['exported']} articles → {updates_path}")
            )

        if result.get("nhsrcl_error") and not result.get("nhsrcl"):
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS("sync_news complete."))