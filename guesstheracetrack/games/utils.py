import uuid
from pathlib import Path

from django.utils.deconstruct import deconstructible
from PIL import Image


@deconstructible
class RandomFileName:
    def __init__(self, path):
        self.path = Path(path)

    def __call__(self, _, filename):
        extension = Path(filename).suffix
        new_filename = f"{uuid.uuid4()}{extension}"
        return self.path / new_filename


def segment_image(image_path, segments):
    image = Image.open(image_path)
    width, height = image.size
    segment_width = width // segments
    segment_height = height // segments
    segments_list = []

    for i in range(segments):
        for j in range(segments):
            left = i * segment_width
            upper = j * segment_height
            right = left + segment_width
            lower = upper + segment_height
            segment = image.crop((left, upper, right, lower))
            segments_list.append(segment)

    return segments_list
