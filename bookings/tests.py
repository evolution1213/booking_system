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