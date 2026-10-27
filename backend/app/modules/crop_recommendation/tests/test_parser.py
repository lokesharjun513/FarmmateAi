import json
from uuid import uuid4

import pytest

from app.modules.crop_recommendation.parser import (
    RecommendationParser,
)

from app.shared.exceptions import ValidationError


FARM_ID = uuid4()


def valid_ai_response():

    return {
        "recommended_sowing_date": "2026-08-20",
        "recommended_crops": [
            {
                "crop_name": "Rice",
                "confidence": 95,
                "reason": "Suitable for the current farming conditions.",
            },
            {
                "crop_name": "Maize",
                "confidence": 80,
                "reason": "Good alternative under the current conditions.",
            },
            {
                "crop_name": "Groundnut",
                "confidence": 70,
                "reason": "Reasonable option if soil conditions are suitable.",
            },
        ],
    }


def response_text():

    return json.dumps(
        valid_ai_response(),
    )


def test_parse_success():

    parser = RecommendationParser()

    result = parser.parse(
        response_text(),
        farm_id=FARM_ID,
    )

    assert result.farm_id == FARM_ID
    assert result.recommended_sowing_date == "2026-08-20"
    assert len(result.recommended_crops) == 3
    assert result.recommended_crops[0].crop_name == "Rice"


def test_parse_preserves_all_fields():

    parser = RecommendationParser()

    result = parser.parse(
        response_text(),
        farm_id=FARM_ID,
    )

    first = result.recommended_crops[0]

    assert first.crop_name == "Rice"
    assert first.confidence == 95
    assert (
        first.reason
        == "Suitable for the current farming conditions."
    )


def test_parse_preserves_farm_id():

    parser = RecommendationParser()

    result = parser.parse(
        response_text(),
        farm_id=FARM_ID,
    )

    assert result.farm_id == FARM_ID


def test_parse_json_code_fence():

    parser = RecommendationParser()

    response = (
        "```json\n"
        + response_text()
        + "\n```"
    )

    result = parser.parse(
        response,
        farm_id=FARM_ID,
    )

    assert len(result.recommended_crops) == 3


def test_parse_generic_code_fence():

    parser = RecommendationParser()

    response = (
        "```\n"
        + response_text()
        + "\n```"
    )

    result = parser.parse(
        response,
        farm_id=FARM_ID,
    )

    assert len(result.recommended_crops) == 3


def test_parse_handles_whitespace():

    parser = RecommendationParser()

    response = (
        "   \n"
        + response_text()
        + "\n   "
    )

    result = parser.parse(
        response,
        farm_id=FARM_ID,
    )

    assert result.recommended_sowing_date == "2026-08-20"


@pytest.mark.parametrize(
    "response",
    [
        "",
        "   ",
        None,
    ],
)
def test_parse_empty_response_fails(
    response,
):

    parser = RecommendationParser()

    with pytest.raises(ValidationError):

        parser.parse(
            response,
            farm_id=FARM_ID,
        )


@pytest.mark.parametrize(
    "response",
    [
        "{invalid json}",
        "This is not JSON",
        "{'recommended_crops': []}",
    ],
)
def test_parse_invalid_json_fails(
    response,
):

    parser = RecommendationParser()

    with pytest.raises(ValidationError):

        parser.parse(
            response,
            farm_id=FARM_ID,
        )


@pytest.mark.parametrize(
    "response",
    [
        "[]",
        '"hello"',
        "123",
        "null",
    ],
)
def test_parse_non_object_json_fails(
    response,
):

    parser = RecommendationParser()

    with pytest.raises(ValidationError):

        parser.parse(
            response,
            farm_id=FARM_ID,
        )


def test_parse_missing_sowing_date_fails():

    data = valid_ai_response()

    data.pop("recommended_sowing_date")

    parser = RecommendationParser()

    with pytest.raises(ValidationError):

        parser.parse(
            json.dumps(data),
            farm_id=FARM_ID,
        )


def test_parse_invalid_sowing_date_type_fails():

    data = valid_ai_response()

    data["recommended_sowing_date"] = 123

    parser = RecommendationParser()

    with pytest.raises(ValidationError):

        parser.parse(
            json.dumps(data),
            farm_id=FARM_ID,
        )


def test_parse_invalid_sowing_date_length_fails():

    data = valid_ai_response()

    data["recommended_sowing_date"] = "2026"

    parser = RecommendationParser()

    with pytest.raises(ValidationError):

        parser.parse(
            json.dumps(data),
            farm_id=FARM_ID,
        )


def test_parse_missing_recommendations_fails():

    data = valid_ai_response()

    data.pop("recommended_crops")

    parser = RecommendationParser()

    with pytest.raises(ValidationError):

        parser.parse(
            json.dumps(data),
            farm_id=FARM_ID,
        )

@pytest.mark.parametrize(
    "count",
    [0, 1, 2, 4, 5],
)
def test_parse_requires_exactly_three_recommendations(
    count,
):

    base_crops = valid_ai_response()[
        "recommended_crops"
    ]

    if count <= 3:

        crops = base_crops[:count]

    else:

        crops = base_crops + [
            {
                "crop_name": f"Crop {i}",
                "confidence": 50,
                "reason": "Alternative crop.",
            }
            for i in range(count - 3)
        ]

    data = valid_ai_response()

    data["recommended_crops"] = crops

    parser = RecommendationParser()

    with pytest.raises(ValidationError):

        parser.parse(
            json.dumps(data),
            farm_id=FARM_ID,
        )


def test_parse_missing_crop_name_fails():

    data = valid_ai_response()

    data["recommended_crops"][0].pop(
        "crop_name",
    )

    parser = RecommendationParser()

    with pytest.raises(ValidationError):

        parser.parse(
            json.dumps(data),
            farm_id=FARM_ID,
        )


def test_parse_missing_confidence_fails():

    data = valid_ai_response()

    data["recommended_crops"][0].pop(
        "confidence",
    )

    parser = RecommendationParser()

    with pytest.raises(ValidationError):

        parser.parse(
            json.dumps(data),
            farm_id=FARM_ID,
        )


def test_parse_invalid_confidence_fails():

    data = valid_ai_response()

    data["recommended_crops"][0]["confidence"] = 101

    parser = RecommendationParser()

    with pytest.raises(ValidationError):

        parser.parse(
            json.dumps(data),
            farm_id=FARM_ID,
        )


def test_parse_missing_reason_fails():

    data = valid_ai_response()

    data["recommended_crops"][0].pop(
        "reason",
    )

    parser = RecommendationParser()

    with pytest.raises(ValidationError):

        parser.parse(
            json.dumps(data),
            farm_id=FARM_ID,
        )


def test_parse_invalid_recommendation_object_fails():

    data = valid_ai_response()

    data["recommended_crops"][0] = "Rice"

    parser = RecommendationParser()

    with pytest.raises(ValidationError):

        parser.parse(
            json.dumps(data),
            farm_id=FARM_ID,
        )


def test_parse_rejects_non_string_response():

    parser = RecommendationParser()

    with pytest.raises(ValidationError):

        parser.parse(
            123,
            farm_id=FARM_ID,
        )


def test_clean_response_without_code_fence():

    parser = RecommendationParser()

    result = parser._clean_response(
        response_text(),
    )

    assert result == response_text()