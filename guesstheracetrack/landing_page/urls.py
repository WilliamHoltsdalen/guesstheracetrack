from django.urls import path

from .views import landing_page
from .views import privacy_policy

app_name = "landing_page"
urlpatterns = [
    path("", view=landing_page, name="landing_page"),
    path("privacy_policy/", view=privacy_policy, name="privacy_policy"),
]
