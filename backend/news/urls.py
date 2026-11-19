from django.urls import path

from news import views

urlpatterns = [
    path("news/", views.news_list, name="news-list"),
    path("news/<slug:slug>/", views.news_detail, name="news-detail"),
]