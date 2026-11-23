import io
from pathlib import Path
from typing import Tuple
from PIL import Image
from google.genai import types


class ImageProcessorException(Exception):
    pass


class ImageProcessor:
    SUPPORTED_MIME_TYPES = {
        "image/jpeg": "JPEG",
        "image/jpg": "JPEG",
        "image/png": "PNG",
        "image/webp": "WEBP"
    }

    def validate_and_inspect_image(self, file_bytes: bytes) -> Tuple[str, int, int]:
        try:
            image_stream = io.BytesIO(file_bytes)
            with Image.open(image_stream) as img:
                img.verify()
                image_format = img.format
                width, height = img.size

            if image_format not in ("JPEG", "PNG", "WEBP"):
                raise ImageProcessorException(f"Unsupported image format: {image_format}")

            return image_format, width, height
        except Exception as error:
            raise ImageProcessorException(f"Invalid image file: {str(error)}")

    def build_gemini_image_part(self, file_path: Path, mime_type: str) -> types.Part:
        if not file_path.exists():
            raise ImageProcessorException(f"Image file does not exist at {file_path}")

        with open(file_path, "rb") as stream:
            image_bytes = stream.read()

        normalized_mime = mime_type if mime_type in self.SUPPORTED_MIME_TYPES else "image/jpeg"
        return types.Part.from_bytes(data=image_bytes, mime_type=normalized_mime)


image_processor = ImageProcessor()
