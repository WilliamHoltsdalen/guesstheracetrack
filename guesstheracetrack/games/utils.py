import uuid
from pathlib import Path

from django.conf import settings
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


@deconstructible
class SegmentImage:
    def __init__(self, image_path, segment_count):
        self.full_image_path = "/app/guesstheracetrack" + image_path
        self.segment_count = segment_count

    def __call__(self):
        return self.segment_image()

    def segment_image(self):
        image = Image.open(self.full_image_path)
        width, height = image.size
        segment_width = width // self.segment_count
        segment_height = height // self.segment_count
        segments_list = []

        for i in range(self.segment_count):
            for j in range(self.segment_count):
                left = i * segment_width
                upper = j * segment_height
                right = left + segment_width
                lower = upper + segment_height
                segment = image.crop((left, upper, right, lower))

                # Save the segment to MEDIA_ROOT
                segment_filename = f"segments/segment_{i}_{j}.png"
                segment_path = Path(settings.URL) / segment_filename
                segment_full_path = Path(settings.MEDIA_ROOT) / segment_filename
                segment.save(segment_full_path)

                segments_list.append(segment_path)

        return segments_list
