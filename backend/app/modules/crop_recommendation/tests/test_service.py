from uuid import uuid4

import pytest

from app.modules.crop_recommendation.service import (
    CropRecommendationService,
)

from app.modules.crop_recommendation.schemas import (
    CropRecommendationResponse,
)


FARM_ID = uuid4()


class FakeContextBuilder:

    def __init__(
        self,
        context,
    ):

        self.context = context
        self.received_farm_id = None

    async def build(
        self,
        farm_id,
    ):

        self.received_farm_id = farm_id

        return self.context


class FakePlanner:

    def __init__(
        self,
        response,
    ):

        self.response = response
        self.received_context = None

    async def recommend(
        self,
        *,
        context,
    ):

        self.received_context = context

        return self.response


class FakeParser:

    def __init__(
        self,
        result,
    ):

        self.result = result
        self.received_response = None
        self.received_farm_id = None

    def parse(
        self,
        response,
        *,
        farm_id,
    ):

        self.received_response = response
        self.received_farm_id = farm_id

        return self.result


def valid_result():

    return CropRecommendationResponse(
        farm_id=FARM_ID,
        recommended_sowing_date="2026-08-20",
        recommended_crops=[
            {
                "crop_name": "Rice",
                "confidence": 95,
                "reason": "Suitable crop.",
            },
            {
                "crop_name": "Maize",
                "confidence": 80,
                "reason": "Good alternative.",
            },
            {
                "crop_name": "Groundnut",
                "confidence": 70,
                "reason": "Another suitable option.",
            },
        ],
    )


@pytest.mark.asyncio
async def test_recommend_success():

    service = CropRecommendationService(
        farm_repository=None,
        weather_service=None,
    )

    context = object()

    builder = FakeContextBuilder(
        context,
    )

    planner = FakePlanner(
        '{"recommendation":"data"}',
    )

    parser = FakeParser(
        valid_result(),
    )

    service.context_builder = builder
    service.planner = planner
    service.parser = parser

    result = await service.recommend(
        farm_id=FARM_ID,
    )

    assert result == parser.result


@pytest.mark.asyncio
async def test_recommend_passes_farm_id_to_context_builder():

    service = CropRecommendationService(
        farm_repository=None,
        weather_service=None,
    )

    builder = FakeContextBuilder(
        object(),
    )

    planner = FakePlanner(
        "AI response",
    )

    parser = FakeParser(
        valid_result(),
    )

    service.context_builder = builder
    service.planner = planner
    service.parser = parser

    await service.recommend(
        farm_id=FARM_ID,
    )

    assert builder.received_farm_id == FARM_ID


@pytest.mark.asyncio
async def test_recommend_passes_context_to_planner():

    service = CropRecommendationService(
        farm_repository=None,
        weather_service=None,
    )

    context = object()

    builder = FakeContextBuilder(
        context,
    )

    planner = FakePlanner(
        "AI response",
    )

    parser = FakeParser(
        valid_result(),
    )

    service.context_builder = builder
    service.planner = planner
    service.parser = parser

    await service.recommend(
        farm_id=FARM_ID,
    )

    assert planner.received_context is context


@pytest.mark.asyncio
async def test_recommend_passes_ai_response_to_parser():

    service = CropRecommendationService(
        farm_repository=None,
        weather_service=None,
    )

    builder = FakeContextBuilder(
        object(),
    )

    planner = FakePlanner(
        "AI RESPONSE",
    )

    parser = FakeParser(
        valid_result(),
    )

    service.context_builder = builder
    service.planner = planner
    service.parser = parser

    await service.recommend(
        farm_id=FARM_ID,
    )

    assert parser.received_response == "AI RESPONSE"


@pytest.mark.asyncio
async def test_recommend_passes_farm_id_to_parser():

    service = CropRecommendationService(
        farm_repository=None,
        weather_service=None,
    )

    service.context_builder = FakeContextBuilder(
        object(),
    )

    service.planner = FakePlanner(
        "AI RESPONSE",
    )

    parser = FakeParser(
        valid_result(),
    )

    service.parser = parser

    await service.recommend(
        farm_id=FARM_ID,
    )

    assert parser.received_farm_id == FARM_ID


@pytest.mark.asyncio
async def test_recommend_returns_parser_result():

    service = CropRecommendationService(
        farm_repository=None,
        weather_service=None,
    )

    expected = valid_result()

    service.context_builder = FakeContextBuilder(
        object(),
    )

    service.planner = FakePlanner(
        "AI RESPONSE",
    )

    service.parser = FakeParser(
        expected,
    )

    result = await service.recommend(
        farm_id=FARM_ID,
    )

    assert result is expected


@pytest.mark.asyncio
async def test_recommend_propagates_context_builder_error():

    service = CropRecommendationService(
        farm_repository=None,
        weather_service=None,
    )

    class FailingBuilder:

        async def build(
            self,
            farm_id,
        ):

            raise RuntimeError(
                "context failed",
            )

    service.context_builder = FailingBuilder()

    with pytest.raises(RuntimeError):

        await service.recommend(
            farm_id=FARM_ID,
        )


@pytest.mark.asyncio
async def test_recommend_propagates_planner_error():

    service = CropRecommendationService(
        farm_repository=None,
        weather_service=None,
    )

    service.context_builder = FakeContextBuilder(
        object(),
    )

    class FailingPlanner:

        async def recommend(
            self,
            *,
            context,
        ):

            raise RuntimeError(
                "planner failed",
            )

    service.planner = FailingPlanner()

    with pytest.raises(RuntimeError):

        await service.recommend(
            farm_id=FARM_ID,
        )


@pytest.mark.asyncio
async def test_recommend_propagates_parser_error():

    service = CropRecommendationService(
        farm_repository=None,
        weather_service=None,
    )

    service.context_builder = FakeContextBuilder(
        object(),
    )

    service.planner = FakePlanner(
        "AI RESPONSE",
    )

    class FailingParser:

        def parse(
            self,
            response,
            *,
            farm_id,
        ):

            raise RuntimeError(
                "parser failed",
            )

    service.parser = FailingParser()

    with pytest.raises(RuntimeError):

        await service.recommend(
            farm_id=FARM_ID,
        )