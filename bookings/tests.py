from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from .models import Room, Booking


class BookingModelTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(name='Test Room', capacity=4, price_per_hour=10.0)

    def test_overlap_prevents_double_booking(self):
        now = timezone.now()
        b1 = Booking.objects.create(room=self.room, start_time=now + timedelta(hours=1), end_time=now + timedelta(hours=2))
        b2 = Booking(room=self.room, start_time=now + timedelta(hours=1, minutes=30), end_time=now + timedelta(hours=2, minutes=30))
        with self.assertRaises(Exception):
            b2.full_clean()

    def test_booking_save_and_send_confirmation(self):
        now = timezone.now()
        b = Booking.objects.create(room=self.room, start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=1), guest_email='test@example.com')
        # send_confirmation should not raise
        b.send_confirmation()
        self.assertEqual(b.room, self.room)

    def test_room_list_requires_login(self):
        resp = self.client.get(reverse('room_list'))
        # should redirect to login (next should be set to /rooms/)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/login/', resp['Location'])
        self.assertIn('next=/rooms/', resp['Location'])


from django.core.management import call_command
from django.contrib.auth.models import User
from .models import City, Location, RoomType


class RandomRoomViewTests(TestCase):
    def setUp(self):
        t = RoomType.objects.create(name='T')
        self.city1 = City.objects.create(name='CityA')
        self.city2 = City.objects.create(name='CityB')
        loc1 = Location.objects.create(city=self.city1, name='Center', latitude=50.4501, longitude=30.5234)
        loc2 = Location.objects.create(city=self.city2, name='Harbor', latitude=46.4846, longitude=30.7326)
        Room.objects.create(name='A1', type=t, capacity=2, price_per_hour=10.0, city=self.city1, location=loc1)
        Room.objects.create(name='B1', type=t, capacity=3, price_per_hour=20.0, city=self.city2, location=loc2)

    def test_random_room_without_filters(self):
        resp = self.client.get(reverse('random_room'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '🎲')

    def test_random_room_with_city_filter(self):
        resp = self.client.get(reverse('random_room'), {'city': self.city1.id})
        self.assertEqual(resp.status_code, 200)
        # Should prefer city1 room if available
        self.assertContains(resp, 'A1')

    def test_rooms_map_api_returns_coords(self):
        resp = self.client.get(reverse('api_rooms_map'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('rooms', data)
        self.assertTrue(len(data['rooms']) >= 1)
        r = data['rooms'][0]
        self.assertIn('lat', r)
        self.assertIn('lng', r)


class GenerateRandomRoomsCommandTests(TestCase):
    def test_generate_command_creates_data(self):
        call_command('generate_random_rooms', cities=2, rooms=5)
        self.assertTrue(City.objects.count() >= 1)
        self.assertTrue(Room.objects.count() >= 1)


class RandomQuickBookTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', password='pass')
        t = RoomType.objects.create(name='T')
        city = City.objects.create(name='C')
        loc = Location.objects.create(city=city, name='L')
        self.room = Room.objects.create(name='R1', type=t, capacity=2, price_per_hour=10.0, city=city, location=loc)

    def test_quick_book_requires_login(self):
        start = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        end = (timezone.now() + timedelta(days=1, hours=1)).strftime('%Y-%m-%dT%H:%M')
        resp = self.client.post(reverse('random_quick_book'), {'room': self.room.id, 'start_time': start, 'end_time': end})
        # Should redirect to login
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/login/', resp['Location'])

    def test_quick_book_creates_booking(self):
        self.client.login(username='u', password='pass')
        start = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        end = (timezone.now() + timedelta(days=1, hours=1)).strftime('%Y-%m-%dT%H:%M')
        resp = self.client.post(reverse('random_quick_book'), {'room': self.room.id, 'start_time': start, 'end_time': end}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Booking.objects.filter(room=self.room).exists())

    def test_quick_book_ajax_creates_booking(self):
        self.client.login(username='u', password='pass')
        start = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        end = (timezone.now() + timedelta(days=1, hours=1)).strftime('%Y-%m-%dT%H:%M')
        resp = self.client.post(reverse('random_quick_book'), {'room': self.room.id, 'start_time': start, 'end_time': end}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertTrue(Booking.objects.filter(room=self.room).exists())


class RoomListAjaxTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ajax', password='pass')
        t = RoomType.objects.create(name='T')
        city = City.objects.create(name='AJCity')
        loc = Location.objects.create(city=city, name='L')
        for i in range(12):
            Room.objects.create(name=f'Room {i+1}', type=t, capacity=2, price_per_hour=10.0 + i, city=city, location=loc)

    def test_ajax_pagination_returns_json(self):
        self.client.login(username='ajax', password='pass')
        resp = self.client.get(reverse('room_list'), {'page': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('html', data)
        self.assertIn('has_next', data)
        self.assertTrue(data['has_next'])

    def test_search_filter_works(self):
        self.client.login(username='ajax', password='pass')
        resp = self.client.get(reverse('room_list'), {'search': 'Room 1'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = resp.json()
        self.assertIn('Room 1', data['html'])