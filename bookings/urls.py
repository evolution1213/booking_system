from django.urls import path
from . import views

urlpatterns = [
    path('', views.room_list, name='room_list'),
    path('random/', views.random_room, name='random_room'),
    path('random/book/', views.random_quick_book, name='random_quick_book'),
    path('api/rooms_map/', views.rooms_map_api, name='api_rooms_map'),

    path('<int:pk>/', views.room_detail, name='room_detail'),
]
