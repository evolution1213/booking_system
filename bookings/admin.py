from django.contrib import admin
from .models import Room, Booking, RoomType, City, Location

@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'latitude', 'longitude')
    list_filter = ('city',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'capacity', 'price_per_hour', 'city', 'location')
    list_filter = ('type', 'city')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('room', 'user', 'guest_name', 'guest_email', 'start_time', 'end_time', 'status')
    list_filter = ('room', 'status', 'start_time')
    search_fields = ('guest_name', 'guest_email')