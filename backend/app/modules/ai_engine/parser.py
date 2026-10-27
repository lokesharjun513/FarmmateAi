import json

from app.modules.advisor.schemas import (
    DailyAdvisorResponse,
)

from app.modules.crop_planner.schemas import (
    CropPlanResponse,
)

from app.shared.exceptions import ValidationError


class AIResponseParser:

    # ========================================================
    # PARSE CROP PLAN
    # ========================================================

    @staticmethod
    def parse_crop_plan(
        response: str,
    ) -> CropPlanResponse:

        if not response:
            raise ValidationError(
                "AI returned an empty response."
            )

        cleaned_response = (
            response
            .strip()
        )

        # ----------------------------------------------------
        # Remove markdown code fences if AI accidentally
        # returns them.
        # ----------------------------------------------------

        if cleaned_response.startswith(
            "```json"
        ):

            cleaned_response = cleaned_response[
                7:
            ]

        elif cleaned_response.startswith(
            "```"
        ):

            cleaned_response = cleaned_response[
                3:
            ]

        if cleaned_response.endswith(
            "```"
        ):

            cleaned_response = cleaned_response[
                :-3
            ]

        cleaned_response = (
            cleaned_response.strip()
        )

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        try:

            data = json.loads(
                cleaned_response,
            )

        except json.JSONDecodeError as exc:

            raise ValidationError(
                "AI returned invalid JSON."
            ) from exc

        # ----------------------------------------------------
        # Validate schema
        # ----------------------------------------------------

        try:

            return CropPlanResponse.model_validate(
                data,
            )

        except Exception as exc:

            raise ValidationError(
                "AI returned an invalid crop plan format."
            ) from exc

    # ========================================================
    # PARSE DAILY ADVICE
    # ========================================================

    @staticmethod
    def parse_daily_advice(
        response: str,
    ) -> DailyAdvisorResponse:

        if not response:
            raise ValidationError(
                "AI returned an empty response."
            )

        cleaned_response = (
            response.strip()
        )

        if cleaned_response.startswith(
            "```json"
        ):

            cleaned_response = (
                cleaned_response[7:]
            )

        elif cleaned_response.startswith(
            "```"
        ):

            cleaned_response = (
                cleaned_response[3:]
            )

        if cleaned_response.endswith(
            "```"
        ):

            cleaned_response = (
                cleaned_response[:-3]
            )

        try:

            data = json.loads(
                cleaned_response.strip(),
            )

        except json.JSONDecodeError as exc:

            raise ValidationError(
                "AI returned invalid JSON."
            ) from exc

        try:

            return DailyAdvisorResponse.model_validate(
                data,
            )

        except Exception as exc:

            raise ValidationError(
                "AI returned an invalid daily advisor format."
            ) from exc