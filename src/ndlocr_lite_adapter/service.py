from __future__ import annotations

import io
import logging
import time

from PIL import Image

from .config import Settings
from .runner import NdlOcrLiteRunner
from .schemas import ImagePayload, ImmichPredictResponse, OcrOptions
from .transform import transform_ndlocr_response

logger = logging.getLogger(__name__)


class OcrService:
    def __init__(self, settings: Settings, runner: NdlOcrLiteRunner | None = None) -> None:
        self.settings = settings
        self.runner = runner or NdlOcrLiteRunner(settings)
        self.request_count = 0

    def predict(self, image_bytes: bytes, options: OcrOptions) -> ImmichPredictResponse:
        self.request_count += 1
        started_at = time.perf_counter()
        image_payload = self._load_image(image_bytes, max_resolution=options.max_resolution)
        ndlocr_response = self.runner.run(image_payload.data)
        result = transform_ndlocr_response(
            ndlocr_response,
            image_width=image_payload.width,
            image_height=image_payload.height,
            min_detection_score=options.min_detection_score,
            min_recognition_score=options.min_recognition_score,
        )
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info(
            "predict completed",
            extra={
                "request_count": self.request_count,
                "ocr_elements": len(result.text),
                "elapsed_ms": elapsed_ms,
            },
        )
        return ImmichPredictResponse(
            ocr={
                "text": result.text,
                "box": result.box,
                "boxScore": result.box_score,
                "textScore": result.text_score,
            },
            imageHeight=image_payload.original_height,
            imageWidth=image_payload.original_width,
        )

    def _load_image(self, image_bytes: bytes, *, max_resolution: int) -> ImagePayload:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.load()
            original_width = image.width
            original_height = image.height
            processed = image.convert("RGB")
            processed = self._limit_pixels(processed)
            processed = self._limit_resolution(processed, max_resolution=max_resolution)
            output = io.BytesIO()
            processed.save(output, format="PNG")
            return ImagePayload(
                data=output.getvalue(),
                width=processed.width,
                height=processed.height,
                original_width=original_width,
                original_height=original_height,
            )

    def _limit_pixels(self, image: Image.Image) -> Image.Image:
        total_pixels = image.width * image.height
        if total_pixels <= self.settings.max_image_pixels:
            return image

        scale = (self.settings.max_image_pixels / float(total_pixels)) ** 0.5
        new_size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
        logger.warning("Image exceeded MAX_IMAGE_PIXELS and was downscaled", extra={"new_size": new_size})
        return image.resize(new_size, Image.Resampling.LANCZOS)

    def _limit_resolution(self, image: Image.Image, *, max_resolution: int) -> Image.Image:
        longest_side = max(image.width, image.height)
        if max_resolution <= 0 or longest_side <= max_resolution:
            return image

        scale = max_resolution / float(longest_side)
        new_size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
        logger.info("Image exceeded maxResolution and was downscaled", extra={"new_size": new_size})
        return image.resize(new_size, Image.Resampling.LANCZOS)
