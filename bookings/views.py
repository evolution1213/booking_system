from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Room, Booking, RoomType, City, Location
from .forms import BookingForm, RoomFilterForm
from django.utils import timezone
from datetime import timedelta



@login_required
def room_list(request):
    # Filtering by room type, city, search and max price with AJAX pagination
    form = RoomFilterForm(request.GET or None)
    qs = Room.objects.all().select_related('city', 'location', 'type')

    if form.is_valid():
        if form.cleaned_data.get('type'):
            qs = qs.filter(type=form.cleaned_data['type'])
        if form.cleaned_data.get('city'):
            qs = qs.filter(city=form.cleaned_data['city'])
        if form.cleaned_data.get('max_price') is not None:
            qs = qs.filter(price_per_hour__lte=form.cleaned_data['max_price'])
        if form.cleaned_data.get('search'):
            qs = qs.filter(name__icontains=form.cleaned_data['search'])

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(qs.order_by('id'), 8)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Handle AJAX requests for incremental updates
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        html = render_to_string('bookings/_room_cards.html', {'rooms': page_obj})
        return JsonResponse({'html': html, 'has_next': page_obj.has_next()})

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

    # also pass full rooms list so sidebar select shows all rooms
    all_rooms = Room.objects.all().order_by('id')
    return render(request, 'bookings/room_list.html', {'rooms': page_obj, 'filter_form': form, 'all_rooms': all_rooms})


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


def random_room(request):
    """Повертає випадкову кімнату з урахуванням фільтрів: тип, місто, макс. ціна."""
    form = RoomFilterForm(request.GET or None)
    room = None
    city = None
    location = None

    qs = Room.objects.all()
    if form.is_valid():
        if form.cleaned_data.get('type'):
            qs = qs.filter(type=form.cleaned_data['type'])
        if form.cleaned_data.get('city'):
            qs = qs.filter(city=form.cleaned_data['city'])
        if form.cleaned_data.get('max_price') is not None:
            qs = qs.filter(price_per_hour__lte=form.cleaned_data['max_price'])

    # If filters produced results, pick random from them
    room = qs.order_by('?').first()

    # If none, fall back to any random room
    if not room:
        room = Room.objects.order_by('?').first()

    return render(request, 'bookings/random_room.html', {'room': room, 'form': form})


def rooms_map_api(request):
    """Return rooms that have explicit coordinates (safe for displaying on map)."""
    qs = Room.objects.filter(location__latitude__isnull=False, location__longitude__isnull=False).select_related('location', 'city', 'type')
    data = []
    for r in qs:
        data.append({
            'id': r.id,
            'name': r.name,
            'lat': r.location.latitude,
            'lng': r.location.longitude,
            'url': reverse('room_detail', args=[r.id]),
            'city': r.city.name if r.city else None,
            'type': r.type.name if r.type else None,
            'price': str(r.price_per_hour),
        })
    return JsonResponse({'rooms': data})





@login_required
def random_quick_book(request):
    """Handle quick booking submission from random page (POST)."""
    if request.method != 'POST':
        return redirect('random_room')

    room_id = request.POST.get('room')
    start = request.POST.get('start_time')
    end = request.POST.get('end_time')
    try:
        booking = Booking(user=request.user, room_id=room_id, start_time=start, end_time=end)
        booking.full_clean()
        booking.save()
        booking.send_confirmation()
        messages.success(request, 'Бронювання успішно створено!')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
    except Exception as e:
        messages.error(request, f'Помилка при бронюванні: {e}')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
    return redirect('random_room')
