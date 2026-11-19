from django.core.management.base import BaseCommand
from django.db import transaction

from places.models import Place, PlaceSection


class Command(BaseCommand):
    help = "Remove all station place listings and sections (keeps PlaceKind taxonomy)."

    @transaction.atomic
    def handle(self, *args, **options):
        places = Place.objects.count()
        sections = PlaceSection.objects.count()
        Place.objects.all().delete()
        PlaceSection.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(f"Cleared {places} place(s) and {sections} section(s).")
        )