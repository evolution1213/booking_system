from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _


class RoomType(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Тип кімнати"))

    class Meta:
        verbose_name = _("Тип кімнати")
        verbose_name_plural = _("Типи кімнат")

    def __str__(self):
        return self.name


class Room(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва кімнати")
    type = models.ForeignKey(RoomType, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Тип")
    capacity = models.IntegerField(verbose_name="Вмістимість")
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна за годину")
    features = models.TextField(blank=True, verbose_name="Особливості")

    def __str__(self):
        return self.name


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'P', _('Очікується')
        CONFIRMED = 'C', _('Підтверджено')
        CANCELED = 'X', _('Скасовано')

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Користувач")
    guest_name = models.CharField(max_length=200, blank=True, verbose_name="Ім'я гостя")
    guest_email = models.EmailField(blank=True, verbose_name="Email гостя")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name="Кімната")
    start_time = models.DateTimeField(verbose_name="Початок")
    end_time = models.DateTimeField(verbose_name="Кінець")
    status = models.CharField(max_length=1, choices=Status.choices, default=Status.PENDING, verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Basic overlap validation
        overlap = Booking.objects.filter(
            room=self.room,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(pk=self.pk)
        if overlap.exists():
            raise ValidationError("Цей період вже заброньовано!")
        if self.end_time <= self.start_time:
            raise ValidationError("Час закінчення має бути після часу початку.")

    def send_confirmation(self):
        # Send a simple confirmation email if guest_email is present
        if self.guest_email:
            subject = f"Підтвердження бронювання: {self.room.name}"
            message = f"Дякуємо {self.guest_name or 'клієнт'}! Ваше бронювання для {self.room.name} з {self.start_time} по {self.end_time} зареєстровано."
            send_mail(subject, message, None, [self.guest_email], fail_silently=True)

    def __str__(self):
        who = self.user.username if self.user else self.guest_name or self.guest_email or 'Гість'
        return f"{who} - {self.room.name} ({self.start_time})"