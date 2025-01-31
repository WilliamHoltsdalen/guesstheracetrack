from django.urls import path

from .views import landing_page

app_name = "landing_page"
urlpatterns = [
    path("", view=landing_page, name="landing_page"),
]
