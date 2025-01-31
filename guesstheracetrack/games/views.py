from pathlib import Path

from django.shortcuts import render

from guesstheracetrack.config import settings


def home(request):
    """Send the image from media to the template"""
    image_path = Path(settings.MEDIA_ROOT) / "media/racetracks/nurburgring.jpg"
    with image_path.open("rb") as f:
        image_data = f.read()

    context = {
        "image": image_data,
    }
    return render(request, "pages/home.html", context)
