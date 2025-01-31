from django.urls import path

from .views import home

app_name = "games"
urlpatterns = [
    path("", view=home, name="home"),
]
