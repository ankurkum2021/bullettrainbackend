from django.urls import path

from catalog import views

urlpatterns = [
    path("corridors/", views.corridor_list, name="corridor-list"),
    path("stations/", views.station_list, name="station-list"),
]