from django.urls import path

app_name = "games"
urlpatterns = [
    path("", view="home", name="home"),
]
