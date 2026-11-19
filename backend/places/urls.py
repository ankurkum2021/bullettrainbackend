from django.urls import path

from places import views

urlpatterns = [
    path("place-kinds/", views.place_kind_list, name="place-kind-list"),
    path("places/", views.place_list, name="place-list"),
    path("stations/<slug:station_slug>/places/", views.station_places, name="station-places"),
]