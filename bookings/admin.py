from django.contrib import admin
from .models import Room, Booking, RoomType

@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'capacity', 'price_per_hour')
    list_filter = ('type',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('room', 'user', 'guest_name', 'guest_email', 'start_time', 'end_time', 'status')
    list_filter = ('room', 'status', 'start_time')
    search_fields = ('guest_name', 'guest_email')