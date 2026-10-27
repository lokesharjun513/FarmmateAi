import json

import pytest

from app.modules.advisor.schemas import (
    AdvicePriority,
    DailyAdvisorResponse,
)
from app.modules.ai_engine.parser import AIResponseParser
from app.modules.crop_planner.schemas import CropPlanResponse
from app.shared.exceptions import ValidationError


# ============================================================
# DAILY ADVISOR FIXTURES
# ============================================================


@pytest.fixture
def valid_daily_advice_json():

    return """
    {
        "summary": "Rice crop is growing well.",
        "warnings": [
            "Moderate rain probability."
        ],
        "recommendations": [
            "Check soil moisture.",
            "Inspect the crop for pests."
        ],
        "priority": "MEDIUM"
    }
    """


@pytest.fixture
def valid_daily_advice_dict():

    return {
        "summary": "Rice crop is growing well.",
        "warnings": [
            "Moderate rain probability."
        ],
        "recommendations": [
            "Check soil moisture.",
            "Inspect the crop for pests."
        ],
        "priority": "MEDIUM",
    }


# ============================================================
# DAILY ADVISOR - SUCCESS
# ============================================================


def test_parse_daily_advice_success(
    valid_daily_advice_json,
):

    result = AIResponseParser.parse_daily_advice(
        valid_daily_advice_json,
    )

    assert isinstance(
        result,
        DailyAdvisorResponse,
    )

    assert result.summary == (
        "Rice crop is growing well."
    )

    assert result.warnings == [
        "Moderate rain probability."
    ]

    assert result.recommendations == [
        "Check soil moisture.",
        "Inspect the crop for pests.",
    ]

    assert result.priority == AdvicePriority.MEDIUM


def test_parse_daily_advice_preserves_all_fields(
    valid_daily_advice_dict,
):

    result = AIResponseParser.parse_daily_advice(
        json.dumps(valid_daily_advice_dict),
    )

    assert result.model_dump() == valid_daily_advice_dict


# ============================================================
# DAILY ADVISOR - PRIORITIES
# ============================================================


@pytest.mark.parametrize(
    "priority",
    [
        "LOW",
        "MEDIUM",
        "HIGH",
    ],
)
def test_parse_daily_advice_supports_all_priorities(
    priority,
):

    response = f"""
    {{
        "summary": "Farm conditions are normal.",
        "warnings": [],
        "recommendations": [
            "Monitor the crop."
        ],
        "priority": "{priority}"
    }}
    """

    result = AIResponseParser.parse_daily_advice(
        response,
    )

    assert result.priority.value == priority


# ============================================================
# DAILY ADVISOR - WHITESPACE
# ============================================================


def test_parse_daily_advice_handles_whitespace(
    valid_daily_advice_json,
):

    response = (
        "\n\n   "
        + valid_daily_advice_json
        + "   \n\n"
    )

    result = AIResponseParser.parse_daily_advice(
        response,
    )

    assert result.priority == AdvicePriority.MEDIUM


# ============================================================
# DAILY ADVISOR - JSON CODE FENCE
# ============================================================


def test_parse_daily_advice_removes_json_code_fence():

    response = """
```json
{
    "summary": "Check the field today.",
    "warnings": [],
    "recommendations": [
        "Inspect the crop."
    ],
    "priority": "LOW"
}
```
"""

    result = AIResponseParser.parse_daily_advice(
        response,
    )

    assert result.summary == (
        "Check the field today."
    )

    assert result.priority == AdvicePriority.LOW


# ============================================================
# DAILY ADVISOR - GENERIC CODE FENCE
# ============================================================


def test_parse_daily_advice_removes_generic_code_fence():

    response = """
```
{
    "summary": "Monitor the crop.",
    "warnings": [],
    "recommendations": [
        "Check soil moisture."
    ],
    "priority": "LOW"
}
```
"""

    result = AIResponseParser.parse_daily_advice(
        response,
    )

    assert result.summary == (
        "Monitor the crop."
    )


# ============================================================
# DAILY ADVISOR - EMPTY RESPONSE
# ============================================================


@pytest.mark.parametrize(
    "response",
    [
        "",
        None,
    ],
)
def test_parse_daily_advice_empty_response_fails(
    response,
):

    with pytest.raises(
        ValidationError,
        match="AI returned an empty response.",
    ):

        AIResponseParser.parse_daily_advice(
            response,
        )


# ============================================================
# DAILY ADVISOR - INVALID JSON
# ============================================================


@pytest.mark.parametrize(
    "response",
    [
        "{invalid json}",
        "{'summary': 'Invalid JSON'}",
        "This is not JSON",
    ],
)
def test_parse_daily_advice_invalid_json_fails(
    response,
):

    with pytest.raises(
        ValidationError,
        match="AI returned invalid JSON.",
    ):

        AIResponseParser.parse_daily_advice(
            response,
        )

def test_parse_daily_advice_valid_json_invalid_structure_fails():

    response = "[1, 2, 3]"

    with pytest.raises(
        ValidationError,
        match="AI returned an invalid daily advisor format.",
    ):

        AIResponseParser.parse_daily_advice(
            response,
        )

# ============================================================
# DAILY ADVISOR - MISSING FIELDS
# ============================================================


def test_parse_daily_advice_missing_summary_fails():

    response = """
    {
        "warnings": [],
        "recommendations": [
            "Inspect the crop."
        ],
        "priority": "LOW"
    }
    """

    with pytest.raises(
        ValidationError,
        match="AI returned an invalid daily advisor format.",
    ):

        AIResponseParser.parse_daily_advice(
            response,
        )


def test_parse_daily_advice_missing_warnings_fails():

    response = """
    {
        "summary": "Monitor the crop.",
        "recommendations": [
            "Inspect the crop."
        ],
        "priority": "LOW"
    }
    """

    with pytest.raises(
        ValidationError,
        match="AI returned an invalid daily advisor format.",
    ):

        AIResponseParser.parse_daily_advice(
            response,
        )


def test_parse_daily_advice_missing_recommendations_fails():

    response = """
    {
        "summary": "Monitor the crop.",
        "warnings": [],
        "priority": "LOW"
    }
    """

    with pytest.raises(
        ValidationError,
        match="AI returned an invalid daily advisor format.",
    ):

        AIResponseParser.parse_daily_advice(
            response,
        )


def test_parse_daily_advice_missing_priority_fails():

    response = """
    {
        "summary": "Monitor the crop.",
        "warnings": [],
        "recommendations": [
            "Inspect the crop."
        ]
    }
    """

    with pytest.raises(
        ValidationError,
        match="AI returned an invalid daily advisor format.",
    ):

        AIResponseParser.parse_daily_advice(
            response,
        )


# ============================================================
# DAILY ADVISOR - INVALID PRIORITY
# ============================================================


def test_parse_daily_advice_invalid_priority_fails():

    response = """
    {
        "summary": "Monitor the crop.",
        "warnings": [],
        "recommendations": [
            "Inspect the crop."
        ],
        "priority": "URGENT"
    }
    """

    with pytest.raises(
        ValidationError,
        match="AI returned an invalid daily advisor format.",
    ):

        AIResponseParser.parse_daily_advice(
            response,
        )


def test_parse_daily_advice_lowercase_priority_fails():

    response = """
    {
        "summary": "Monitor the crop.",
        "warnings": [],
        "recommendations": [
            "Inspect the crop."
        ],
        "priority": "low"
    }
    """

    with pytest.raises(
        ValidationError,
        match="AI returned an invalid daily advisor format.",
    ):

        AIResponseParser.parse_daily_advice(
            response,
        )


# ============================================================
# DAILY ADVISOR - INVALID FIELD TYPES
# ============================================================


@pytest.mark.parametrize(
    "field,value",
    [
        ("summary", 123),
        ("warnings", "not a list"),
        ("recommendations", "not a list"),
        ("priority", 123),
    ],
)
def test_parse_daily_advice_invalid_field_type_fails(
    field,
    value,
):

    data = {
        "summary": "Monitor the crop.",
        "warnings": [],
        "recommendations": [
            "Inspect the crop."
        ],
        "priority": "LOW",
    }

    data[field] = value

    response = json.dumps(data)

    with pytest.raises(
        ValidationError,
        match="AI returned an invalid daily advisor format.",
    ):

        AIResponseParser.parse_daily_advice(
            response,
        )


# ============================================================
# DAILY ADVISOR - MALFORMED CODE FENCE
# ============================================================


def test_parse_daily_advice_opening_code_fence_without_closing_fence():

    response = """
```json
{
    "summary": "Monitor the crop.",
    "warnings": [],
    "recommendations": [
        "Inspect the crop."
    ],
    "priority": "LOW"
}
"""

    result = AIResponseParser.parse_daily_advice(
        response,
    )

    assert result.summary == "Monitor the crop."

    assert result.priority == (
        AdvicePriority.LOW
    )

# ============================================================
# DAILY ADVISOR - EXTRA FIELDS
# ============================================================


def test_parse_daily_advice_allows_extra_fields():

    response = """
    {
        "summary": "Monitor the crop.",
        "warnings": [],
        "recommendations": [
            "Inspect the crop."
        ],
        "priority": "LOW",
        "extra_field": "ignored"
    }
    """

    result = AIResponseParser.parse_daily_advice(
        response,
    )

    assert result.priority == AdvicePriority.LOW


# ============================================================
# CROP PLAN - BASIC REGRESSION
# ============================================================


def test_parse_crop_plan_empty_response_fails():

    with pytest.raises(
        ValidationError,
        match="AI returned an empty response.",
    ):

        AIResponseParser.parse_crop_plan("")


def test_parse_crop_plan_invalid_json_fails():

    with pytest.raises(
        ValidationError,
        match="AI returned invalid JSON.",
    ):

        AIResponseParser.parse_crop_plan(
            "{invalid json}"
        )


def test_parse_crop_plan_code_fence_is_removed():

    response = """
```json
{
    "crop_name": "Rice"
}
```
"""

    try:

        result = AIResponseParser.parse_crop_plan(
            response,
        )

        assert isinstance(
            result,
            CropPlanResponse,
        )

    except ValidationError as exc:

        assert (
            str(exc)
            == "AI returned an invalid crop plan format."
        )