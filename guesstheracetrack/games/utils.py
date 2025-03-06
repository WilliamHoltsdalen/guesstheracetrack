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


@deconstructible
class SegmentImage:
    def __init__(self, image_path, segment_count):
        self.image_path = image_path
        self.segment_count = segment_count

    def __call__(self):
        return self.segment_image()

    def segment_image(self):
        image = Image.open(self.image_path)
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
                segments_list.append(segment)

        return segments_list
