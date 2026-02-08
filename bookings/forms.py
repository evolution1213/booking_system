from django import forms
from .models import Booking, RoomType, City

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['guest_name', 'guest_email', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class RoomFilterForm(forms.Form):
    search = forms.CharField(required=False, label='Пошук', widget=forms.TextInput(attrs={'placeholder': 'Пошук за назвою'}))
    type = forms.ModelChoiceField(queryset=RoomType.objects.all(), required=False, label='Тип кімнати')
    city = forms.ModelChoiceField(queryset=City.objects.all(), required=False, label='Місто')
    max_price = forms.DecimalField(required=False, decimal_places=2, max_digits=10, label='Макс. ціна')
