from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException
from fastapi.responses import PlainTextResponse

from .config import Settings, configure_logging, get_settings
from .schemas import ImmichPredictResponse, OcrOptions, OcrRequestEntries
from .service import OcrService

logger = logging.getLogger(__name__)


def create_app(
    settings: Settings | None = None,
    service: OcrService | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    service = service or OcrService(settings)
    app = FastAPI()
    app.state.settings = settings
    app.state.ocr_service = service

    def get_service() -> OcrService:
        return app.state.ocr_service

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "Immich ML"}

    @app.get("/ping")
    async def ping() -> PlainTextResponse:
        return PlainTextResponse("pong")

    @app.post("/predict", response_model=ImmichPredictResponse)
    async def predict(
        entries: str = Form(),
        image: bytes | None = File(default=None),
        ocr_service: OcrService = Depends(get_service),
    ) -> ImmichPredictResponse:
        if image is None:
            raise HTTPException(status_code=400, detail="image is required for OCR requests")

        options = _parse_ocr_options(entries)
        try:
            response = ocr_service.predict(image, options)
        except HTTPException:
            raise
        except TimeoutError as error:
            logger.exception("OCR prediction timed out")
            raise HTTPException(status_code=504, detail="OCR prediction timed out") from error
        except Exception as error:
            logger.exception("OCR prediction failed")
            raise HTTPException(status_code=500, detail="OCR prediction failed") from error
        return response

    return app


def _parse_ocr_options(entries: str) -> OcrOptions:
    try:
        payload: dict[str, Any] = json.loads(entries)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=422, detail="Invalid request format") from error

    if set(payload.keys()) != {"ocr"}:
        raise HTTPException(status_code=501, detail="Only the OCR task is supported")

    try:
        parsed = OcrRequestEntries.model_validate(payload["ocr"])
    except Exception as error:
        raise HTTPException(status_code=422, detail="Invalid OCR request format") from error

    detection_options = parsed.detection.options
    recognition_options = parsed.recognition.options
    return OcrOptions(
        model_name=parsed.recognition.modelName or parsed.detection.modelName,
        min_detection_score=float(detection_options.get("minScore", 0.5)),
        min_recognition_score=float(recognition_options.get("minScore", 0.8)),
        max_resolution=int(detection_options.get("maxResolution", 736)),
    )


app = create_app()
