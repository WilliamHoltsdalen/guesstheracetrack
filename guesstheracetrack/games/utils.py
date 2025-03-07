import hashlib
import os
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
class HashedFileName:
    def __init__(self, path):
        self.path = Path(path)

    def __call__(self, _, filename):
        extension = Path(filename).suffix
        new_filename = f"{hashlib.sha256(filename.encode()).hexdigest()}{extension}"
        return self.path / new_filename


@deconstructible
class SegmentImage:
    def __init__(self, image_path, count_sqroot):
        self.full_image_path = "/app/guesstheracetrack" + image_path
        self.image_path = image_path
        self.count_sq_root = count_sqroot

    def __call__(self):
        return self.segment_image()

    def segment_image(self):
        image = Image.open(self.full_image_path)
        width, height = image.size
        segment_width = width // self.count_sq_root
        segment_height = height // self.count_sq_root
        segments_list = []

        for i in range(self.count_sq_root):
            for j in range(self.count_sq_root):
                left = i * segment_width
                upper = j * segment_height
                right = left + segment_width
                lower = upper + segment_height
                segment = image.crop((left, upper, right, lower))

                hashed_file_name = HashedFileName("segments")
                segment_filename = hashed_file_name(
                    None,
                    Path(self.image_path).name
                    + f"{i}_{j}"
                    + Path(self.image_path).suffix,
                )
                segment_path = os.path.join(settings.MEDIA_URL, segment_filename)  # noqa: PTH118 use of os.path.join is fine here
                segment_full_path = os.path.join(settings.MEDIA_ROOT, segment_filename)  # noqa: PTH118 use of os.path.join is fine here
                segment.save(segment_full_path)

                segments_list.append(
                    {
                        "i": i + 1,
                        "j": j + 1,
                        "segment": segment_path,
                    },
                )

        return segments_list
