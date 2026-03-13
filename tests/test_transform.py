from ndlocr_lite_adapter.transform import transform_ndlocr_response


def test_transform_ndlocr_response_normalizes_boxes_and_scores() -> None:
    payload = {
        "contents": [
            [
                {
                    "boundingBox": [[10, 20], [10, 60], [110, 20], [110, 60]],
                    "confidence": 0.91,
                    "text": "Hello",
                }
            ]
        ]
    }

    result = transform_ndlocr_response(
        payload,
        image_width=200,
        image_height=100,
        min_detection_score=0.5,
        min_recognition_score=0.8,
    )

    assert result.text == ["Hello"]
    assert result.box == [0.05, 0.2, 0.55, 0.2, 0.55, 0.6, 0.05, 0.6]
    assert result.box_score == [0.91]
    assert result.text_score == [0.91]


def test_transform_ndlocr_response_filters_low_confidence_lines() -> None:
    payload = {
        "contents": [
            [
                {
                    "boundingBox": [[0, 0], [0, 10], [10, 0], [10, 10]],
                    "confidence": 0.7,
                    "text": "skip",
                }
            ]
        ]
    }

    result = transform_ndlocr_response(
        payload,
        image_width=100,
        image_height=100,
        min_detection_score=0.8,
        min_recognition_score=0.8,
    )

    assert result.text == []
    assert result.box == []
