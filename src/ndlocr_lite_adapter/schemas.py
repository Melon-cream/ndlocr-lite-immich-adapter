from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


class PipelineEntry(BaseModel):
    modelName: str
    options: dict[str, Any] = Field(default_factory=dict)


class OcrRequestEntries(BaseModel):
    detection: PipelineEntry
    recognition: PipelineEntry


class ImmichOcrPayload(BaseModel):
    text: list[str]
    box: list[float]
    boxScore: list[float]
    textScore: list[float]


class ImmichPredictResponse(BaseModel):
    ocr: ImmichOcrPayload
    imageHeight: int
    imageWidth: int


@dataclass(slots=True)
class OcrOptions:
    model_name: str
    min_detection_score: float
    min_recognition_score: float
    max_resolution: int


@dataclass(slots=True)
class ImagePayload:
    data: bytes
    width: int
    height: int
    original_width: int
    original_height: int


@dataclass(slots=True)
class OcrResult:
    text: list[str]
    box: list[float]
    box_score: list[float]
    text_score: list[float]
