from django.core.management.base import BaseCommand
import random
from bookings.models import City, Location, Room, RoomType

CITY_NAMES = ['Львів', 'Київ', 'Одеса', 'Харків', 'Дніпро', 'Чернівці', 'Вінниця']
LOC_NAMES = ['Старий центр', 'Побережжя', 'Пагорби', 'Район мистецтв', 'Парк', 'Промисловий район']
FEATURES = [
    'З чудовим видом', 'Лофт-стиль', 'Ретро декор', 'З джакузі', 'Тематичний інтер’єр', 'З каміном'
]

class Command(BaseCommand):
    help = 'Генерує тестові міста, локації та кімнати'

    def add_arguments(self, parser):
        parser.add_argument('--cities', type=int, default=5, help='Кількість міст')
        parser.add_argument('--rooms', type=int, default=20, help='Кількість кімнат')

    def handle(self, *args, **options):
        num_cities = options['cities']
        num_rooms = options['rooms']

        created_cities = []
        for i in range(num_cities):
            name = random.choice(CITY_NAMES) + (f' {i}' if i >= len(CITY_NAMES) else '')
            city, _ = City.objects.get_or_create(name=name, defaults={'country': 'UA'})
            created_cities.append(city)
            # create 2-4 locations per city
            for j in range(random.randint(2, 4)):
                loc_name = random.choice(LOC_NAMES) + (f' {j}' if j >= len(LOC_NAMES) else '')
                # Generate random coordinates roughly within Ukraine bounds
                lat = round(random.uniform(44.0, 52.0), 6)
                lon = round(random.uniform(22.0, 40.0), 6)
                Location.objects.get_or_create(city=city, name=loc_name, defaults={'latitude': lat, 'longitude': lon})

        types = list(RoomType.objects.all())
        if not types:
            types = [RoomType.objects.create(name='Стандарт'), RoomType.objects.create(name='Люкс')]

        for i in range(num_rooms):
            city = random.choice(created_cities) if created_cities else None
            locations = list(Location.objects.filter(city=city)) if city else []
            loc = random.choice(locations) if locations else None
            room = Room.objects.create(
                name=f'Кімната {i+1}',
                type=random.choice(types),
                capacity=random.randint(1, 8),
                price_per_hour=round(random.uniform(50, 1000), 2),
                features=', '.join(random.sample(FEATURES, k=random.randint(1, 2))),
                city=city,
                location=loc
            )
        self.stdout.write(self.style.SUCCESS(f'Згенеровано {num_cities} міст та {num_rooms} кімнат'))
