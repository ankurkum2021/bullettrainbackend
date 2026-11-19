import signal
import time

from django.core.management.base import BaseCommand

from news.pipeline.run_sync import run_news_sync
from news.pipeline.sync import repo_root


class Command(BaseCommand):
    help = "Poll NHSRCL press releases and upsert new developments into the database."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._keep_running = True

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=900,
            help="Seconds between polls (default: 900 = 15 minutes).",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Run a single poll and exit (same as sync_nhsrcl without loop).",
        )
        parser.add_argument(
            "--export-json",
            action="store_true",
            help="Refresh data/updates.json after each poll that creates at least one row.",
        )

    def handle(self, *args, **options):
        interval = max(60, options["interval"])

        def stop(*_):
            self._keep_running = False
            self.stdout.write(self.style.WARNING("Stopping watcher …"))

        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)

        updates_path = repo_root() / "data" / "updates.json"

        while True:
            try:
                do_export = bool(options["export_json"])
                result = run_news_sync(
                    skip_nhsrcl=False,
                    backfill_json=False,
                    export_json=do_export,
                    updates_path=updates_path,
                    reprocess=True,
                    prune=True,
                )
                if result.get("nhsrcl"):
                    stats = result["nhsrcl"]
                    self.stdout.write(
                        f"Poll complete — fetched {stats['fetched']}, "
                        f"new {stats['created']}, updated {stats['updated']}, "
                        f"skipped {stats['skipped']}"
                    )
                elif result.get("nhsrcl_error"):
                    self.stderr.write(self.style.ERROR(result["nhsrcl_error"]))
                if do_export and result.get("exported"):
                    self.stdout.write(
                        self.style.SUCCESS(f"Exported {result['exported']} rows → {updates_path}")
                    )
            except Exception as exc:
                self.stderr.write(self.style.ERROR(str(exc)))

            if options["once"] or not self._keep_running:
                break

            self.stdout.write(f"Sleeping {interval}s …")
            for _ in range(interval):
                if not self._keep_running:
                    break
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Watcher exited."))