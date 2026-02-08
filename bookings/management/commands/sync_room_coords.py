from django.core.management.base import BaseCommand
from bookings.models import Room


class Command(BaseCommand):
    help = 'Syncs Room.latitude/longitude from their Location (if present)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without saving')

    def handle(self, *args, **options):
        dry = options['dry_run']
        rooms = Room.objects.select_related('location')
        updated = 0
        skipped = 0
        for r in rooms:
            if r.location and r.location.latitude is not None and r.location.longitude is not None:
                lat = float(r.location.latitude)
                lng = float(r.location.longitude)
                if r.latitude != lat or r.longitude != lng:
                    self.stdout.write(f"Will update: {r.name} ({r.id}) => {lat},{lng}")
                    if not dry:
                        r.latitude = lat
                        r.longitude = lng
                        r.save(update_fields=['latitude', 'longitude'])
                    updated += 1
                else:
                    skipped += 1
            else:
                skipped += 1
        self.stdout.write(self.style.SUCCESS(f"Done. Updated: {updated}. Skipped (no location or unchanged): {skipped}"))
