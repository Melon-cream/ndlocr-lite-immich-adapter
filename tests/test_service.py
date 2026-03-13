from __future__ import annotations

import io

from PIL import Image

from ndlocr_lite_adapter.config import Settings
from ndlocr_lite_adapter.schemas import OcrOptions
from ndlocr_lite_adapter.service import OcrService


class FakeRunner:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.last_image_size: tuple[int, int] | None = None

    def run(self, image_bytes: bytes) -> dict:
        with Image.open(io.BytesIO(image_bytes)) as image:
            self.last_image_size = image.size
        return self.payload


def test_predict_keeps_original_image_dimensions_after_downscale() -> None:
    runner = FakeRunner(
        {
            "contents": [
                [
                    {
                        "boundingBox": [[0, 0], [0, 100], [200, 0], [200, 100]],
                        "confidence": 0.95,
                        "text": "scaled",
                    }
                ]
            ]
        }
    )
    settings = Settings(max_image_pixels=10_000)
    service = OcrService(settings, runner=runner)

    result = service.predict(_png_bytes(width=400, height=200), _options(max_resolution=400))

    assert runner.last_image_size == (141, 70)
    assert result.imageWidth == 400
    assert result.imageHeight == 200
    assert result.ocr.box == [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]


def _options(*, max_resolution: int) -> OcrOptions:
    return OcrOptions(
        model_name="NDLOCR-Lite",
        min_detection_score=0.5,
        min_recognition_score=0.8,
        max_resolution=max_resolution,
    )


def _png_bytes(*, width: int, height: int) -> bytes:
    image = Image.new("RGB", (width, height), color="white")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
