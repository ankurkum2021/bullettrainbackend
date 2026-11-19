from django.core.management.base import BaseCommand
from django.db import transaction

from places.models import PlaceKind

DEFAULT_KINDS = [
    ("transport", "Transport & mobility", "Cabs, airport runs, shuttles", "cab", 10),
    ("lodging", "Lodging", "Hotels, serviced stays, guest houses", "hotel", 20),
    ("food_and_drink", "Food & drink", "Restaurants, cafés, catering", "restaurant", 30),
    ("industry", "Industry & workplaces", "MIDC, plants, trade clusters", "midc", 40),
    ("commerce", "Commerce & markets", "Bourses, wholesale, retail hubs", "pin", 50),
    ("logistics", "Ports & logistics", "Ports, freight, ICDs", "highway", 60),
    ("aviation", "Aviation", "Airports and aerotropolis links", "airport", 70),
    ("landmark", "Landmarks", "Museums, heritage, public venues", "pin", 80),
    ("other", "Other", "Anything not covered above", "info", 90),
]


class Command(BaseCommand):
    help = "Seed generic PlaceKind taxonomy."

    @transaction.atomic
    def handle(self, *args, **options):
        created = updated = 0
        for slug, label, description, icon, order in DEFAULT_KINDS:
            _, was_created = PlaceKind.objects.update_or_create(
                slug=slug,
                defaults={
                    "label": label,
                    "description": description,
                    "icon": icon,
                    "sort_order": order,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Place kinds: {created} created, {updated} updated."))