from django.core.management.base import BaseCommand
from django.db.models import Q
import random

from bookings.models import City, Location, Room


class Command(BaseCommand):
    help = 'Assigns a city and location to rooms that are missing them.'

    def add_arguments(self, parser):
        parser.add_argument('--assign-random', action='store_true', help='Assign random existing city/location')
        parser.add_argument('--default-city-name', type=str, default='Невідоме місто', help='Name for default city when none exist')
        parser.add_argument('--default-location-name', type=str, default='Невідома локація', help='Name for default location when none exist')

    def handle(self, *args, **options):
        assign_random = options['assign_random']
        default_city_name = options['default_city_name']
        default_location_name = options['default_location_name']

        rooms_qs = Room.objects.filter(Q(city__isnull=True) | Q(location__isnull=True))
        total = rooms_qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('Немає кімнат без міста або локації.'))
            return

        cities = list(City.objects.all())
        created_cities = 0
        created_locations = 0
        updated = 0

        for room in rooms_qs:
            changed = False
            if room.city is None:
                if cities:
                    city = random.choice(cities) if assign_random else cities[0]
                else:
                    city, _ = City.objects.get_or_create(name=default_city_name, defaults={'country': 'UA'})
                    cities.append(city)
                    created_cities += 1
                room.city = city
                changed = True

            if room.location is None:
                locations = list(Location.objects.filter(city=room.city))
                if locations:
                    loc = random.choice(locations) if assign_random else locations[0]
                else:
                    loc, _ = Location.objects.get_or_create(city=room.city, name=default_location_name)
                    created_locations += 1
                room.location = loc
                changed = True

            if changed:
                room.save()
                updated += 1
                self.stdout.write(self.style.NOTICE(f'Оновлено: {room.name} -> {room.city.name}, {room.location.name}'))

        self.stdout.write(self.style.SUCCESS(f'Завершено: оновлено {updated} з {total} кімнат. (створено міст: {created_cities}, локацій: {created_locations})'))
