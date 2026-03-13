from __future__ import annotations

from typing import Any

from .schemas import OcrResult


def transform_ndlocr_response(
    payload: dict[str, Any],
    *,
    image_width: int,
    image_height: int,
    min_detection_score: float,
    min_recognition_score: float,
) -> OcrResult:
    contents = payload.get("contents", [])
    lines = contents[0] if contents else []

    text: list[str] = []
    box: list[float] = []
    box_score: list[float] = []
    text_score: list[float] = []

    for line in lines:
        raw_text = str(line.get("text", "")).strip()
        if not raw_text:
            continue

        confidence = _clamp_score(line.get("confidence"))
        if confidence < min_detection_score or confidence < min_recognition_score:
            continue

        raw_box = line.get("boundingBox", [])
        normalized_box = _normalize_box(raw_box, image_width=image_width, image_height=image_height)
        if normalized_box is None:
            continue

        text.append(raw_text)
        box.extend(normalized_box)
        box_score.append(confidence)
        text_score.append(confidence)

    return OcrResult(text=text, box=box, box_score=box_score, text_score=text_score)


def _normalize_box(raw_box: Any, *, image_width: int, image_height: int) -> list[float] | None:
    if not isinstance(raw_box, list) or len(raw_box) != 4:
        return None

    try:
        top_left = raw_box[0]
        bottom_left = raw_box[1]
        top_right = raw_box[2]
        bottom_right = raw_box[3]
        points = [top_left, top_right, bottom_right, bottom_left]
        normalized: list[float] = []
        for x, y in points:
            normalized.append(_clamp_coordinate(float(x) / float(image_width)))
            normalized.append(_clamp_coordinate(float(y) / float(image_height)))
        return normalized
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _clamp_coordinate(value: float) -> float:
    return max(0.0, min(1.0, value))


def _clamp_score(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 1.0
    return max(0.0, min(1.0, score))
