from __future__ import annotations

from fastapi.testclient import TestClient

from ndlocr_lite_adapter.app import create_app
from ndlocr_lite_adapter.schemas import ImmichOcrPayload, ImmichPredictResponse


class FakeService:
    def __init__(self, response: ImmichPredictResponse) -> None:
        self.response = response

    def predict(self, image_bytes: bytes, options):  # noqa: ANN001, ANN201
        return self.response


def test_ping() -> None:
    client = TestClient(create_app(service=FakeService(_response())))

    response = client.get("/ping")

    assert response.status_code == 200
    assert response.text == "pong"


def test_predict_returns_immich_compatible_shape() -> None:
    client = TestClient(create_app(service=FakeService(_response())))

    response = client.post(
        "/predict",
        data={"entries": _ocr_entries()},
        files={"image": ("test.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "ocr": {
            "text": ["Hello"],
            "box": [0.05, 0.2, 0.55, 0.2, 0.55, 0.6, 0.05, 0.6],
            "boxScore": [0.91],
            "textScore": [0.91],
        },
        "imageHeight": 100,
        "imageWidth": 200,
    }


def test_predict_rejects_non_ocr_task() -> None:
    client = TestClient(create_app(service=FakeService(_response())))

    response = client.post(
        "/predict",
        data={"entries": '{"clip":{"visual":{"modelName":"ViT-B-32__openai"}}}'},
        files={"image": ("test.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 501


def test_predict_requires_image() -> None:
    client = TestClient(create_app(service=FakeService(_response())))

    response = client.post("/predict", data={"entries": _ocr_entries()})

    assert response.status_code == 400


def test_predict_returns_gateway_timeout_for_timeouts() -> None:
    class TimeoutService:
        def predict(self, image_bytes: bytes, options):  # noqa: ANN001, ANN201
            raise TimeoutError("timed out")

    client = TestClient(create_app(service=TimeoutService()))

    response = client.post(
        "/predict",
        data={"entries": _ocr_entries()},
        files={"image": ("test.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 504


def _response() -> ImmichPredictResponse:
    return ImmichPredictResponse(
        ocr=ImmichOcrPayload(
            text=["Hello"],
            box=[0.05, 0.2, 0.55, 0.2, 0.55, 0.6, 0.05, 0.6],
            boxScore=[0.91],
            textScore=[0.91],
        ),
        imageHeight=100,
        imageWidth=200,
    )


def _ocr_entries() -> str:
    return (
        '{"ocr":{"detection":{"modelName":"NDLOCR-Lite","options":{"minScore":0.5,"maxResolution":736}},'
        '"recognition":{"modelName":"NDLOCR-Lite","options":{"minScore":0.8}}}}'
    )


def _png_bytes() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x002\x08\x02\x00\x00\x00%W\xe9\xe9"
        b"\x00\x00\x00(IDATx\x9cc`\xa0\x1f0\xe1\x95\x1d\xb1\xd2\x00R\x8c\x8cT0j\x18\x35\x8c\x1aF\r\xa3\x86"
        b"Q\xc3\xa8a\xd40j\x00\xa4\xc8\x01d\xf2\xc4\xe2\x8d\x00\x00\x00\x00IEND\xaeB`\x82"
    )
