from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Room, Booking, RoomType
from .forms import BookingForm, RoomFilterForm
from django.utils import timezone
from datetime import timedelta


@login_required
def room_list(request):
    # Filtering by room type
    form = RoomFilterForm(request.GET or None)
    rooms = Room.objects.all()
    if form.is_valid() and form.cleaned_data.get('type'):
        rooms = rooms.filter(type=form.cleaned_data['type'])

    # Quick booking from sidebar (only for authenticated users)
    if request.method == 'POST' and request.POST.get('quick_book'):
        if not request.user.is_authenticated:
            messages.error(request, 'Будь ласка, увійдіть у систему, щоб забронювати швидко.')
            return redirect('login')
        room_id = request.POST.get('room')
        start = request.POST.get('start_time')
        end = request.POST.get('end_time')
        try:
            booking = Booking(user=request.user, room_id=room_id, start_time=start, end_time=end)
            booking.full_clean()
            booking.save()
            booking.send_confirmation()
            messages.success(request, 'Бронювання успішно створено!')
            return redirect('room_list')
        except Exception as e:
            messages.error(request, f'Помилка: {e}')

    return render(request, 'bookings/room_list.html', {'rooms': rooms, 'filter_form': form})


def room_detail(request, pk):
    room = get_object_or_404(Room, pk=pk)
    # show bookings for this room for the upcoming 30 days
    now = timezone.now()
    future = now + timedelta(days=30)
    bookings = Booking.objects.filter(room=room, end_time__gte=now, start_time__lte=future).order_by('start_time')

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.room = room
            if request.user.is_authenticated:
                booking.user = request.user
            # Validation
            try:
                booking.full_clean()
                booking.save()
                booking.send_confirmation()
                messages.success(request, 'Бронювання успішно створено! Підтвердження надіслано на вказаний email (якщо він заданий).')
                return redirect('room_detail', pk=pk)
            except Exception as e:
                form.add_error(None, str(e))
    else:
        form = BookingForm()

    return render(request, 'bookings/room_detail.html', {'room': room, 'form': form, 'bookings': bookings})
