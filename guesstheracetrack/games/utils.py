import uuid
from pathlib import Path

from django.utils.deconstruct import deconstructible


@deconstructible
class RandomFileName:
    def __init__(self, path):
        self.path = Path(path)

    def __call__(self, _, filename):
        extension = Path(filename).suffix
        new_filename = f"{uuid.uuid4()}{extension}"
        return self.path / new_filename
