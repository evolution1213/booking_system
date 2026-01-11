from django import forms
from .models import Booking, RoomType

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['guest_name', 'guest_email', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class RoomFilterForm(forms.Form):
    type = forms.ModelChoiceField(queryset=RoomType.objects.all(), required=False, label='Тип кімнати')
