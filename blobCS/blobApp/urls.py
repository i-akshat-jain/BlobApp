from . import views
from django.urls import path

urlpatterns = [
    path("", views.home, name="home"),
    path("api/mention/", views.mention_list, name="mention_list"),
    ]
