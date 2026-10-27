import json
from uuid import UUID

from app.modules.crop_recommendation.schemas import (
    CropRecommendationResponse,
    RecommendedCrop,
)

from app.shared.exceptions import ValidationError


class RecommendationParser:

    # ========================================================
    # PARSE AI RESPONSE
    # ========================================================

    def parse(
        self,
        response: str,
        *,
        farm_id: UUID,
    ) -> CropRecommendationResponse:

        cleaned_response = self._clean_response(
            response,
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
                "AI returned an invalid JSON response.",
            ) from exc

        # ----------------------------------------------------
        # Validate top-level JSON object
        # ----------------------------------------------------

        if not isinstance(data, dict):

            raise ValidationError(
                "AI recommendation response must be a JSON object.",
            )

        # ----------------------------------------------------
        # Validate sowing date
        # ----------------------------------------------------

        recommended_sowing_date = data.get(
            "recommended_sowing_date",
        )

        if not recommended_sowing_date:

            raise ValidationError(
                "AI recommendation is missing the sowing date.",
            )

        if not isinstance(
            recommended_sowing_date,
            str,
        ):

            raise ValidationError(
                "AI recommendation contains an invalid sowing date.",
            )

        recommended_sowing_date = (
            recommended_sowing_date.strip()
        )

        if len(recommended_sowing_date) != 10:

            raise ValidationError(
                "AI recommendation contains an invalid sowing date.",
            )

        # ----------------------------------------------------
        # Validate recommendations
        # ----------------------------------------------------

        raw_recommendations = data.get(
            "recommended_crops",
        )

        if not isinstance(
            raw_recommendations,
            list,
        ):

            raise ValidationError(
                "AI recommendation list is invalid.",
            )

        # ----------------------------------------------------
        # FarmMate requires exactly 3 recommendations.
        # ----------------------------------------------------

        if len(raw_recommendations) != 3:

            raise ValidationError(
                "AI must return exactly three crop recommendations.",
            )

        recommendations: list[RecommendedCrop] = []

        # ----------------------------------------------------
        # Parse each crop
        # ----------------------------------------------------

        for index, crop in enumerate(
            raw_recommendations,
            start=1,
        ):

            if not isinstance(
                crop,
                dict,
            ):

                raise ValidationError(
                    f"AI recommendation #{index} is invalid.",
                )

            crop_name = crop.get(
                "crop_name",
            )

            confidence = crop.get(
                "confidence",
            )

            reason = crop.get(
                "reason",
            )

            if not crop_name:

                raise ValidationError(
                    f"AI recommendation #{index} is missing crop name.",
                )

            if confidence is None:

                raise ValidationError(
                    f"AI recommendation #{index} is missing confidence.",
                )

            if not reason:

                raise ValidationError(
                    f"AI recommendation #{index} is missing reason.",
                )

            try:

                recommendation = RecommendedCrop(
                    crop_name=crop_name,
                    confidence=confidence,
                    reason=reason,
                )

            except Exception as exc:

                raise ValidationError(
                    f"AI recommendation #{index} contains invalid data.",
                ) from exc

            recommendations.append(
                recommendation,
            )

        # ----------------------------------------------------
        # Final response validation
        # ----------------------------------------------------

        try:

            return CropRecommendationResponse(
                farm_id=farm_id,
                recommended_sowing_date=(
                    recommended_sowing_date
                ),
                recommended_crops=recommendations,
            )

        except Exception as exc:

            raise ValidationError(
                "AI recommendation response contains invalid data.",
            ) from exc

    # ========================================================
    # CLEAN AI RESPONSE
    # ========================================================

    def _clean_response(
        self,
        response: str,
    ) -> str:

        if not isinstance(
            response,
            str,
        ):

            raise ValidationError(
                "AI returned an invalid response.",
            )

        response = response.strip()

        if not response:

            raise ValidationError(
                "AI returned an empty response.",
            )

        # ----------------------------------------------------
        # Remove markdown code fences.
        #
        # Supports:
        #
        # ```json
        # {...}
        # ```
        #
        # and:
        #
        # ```
        # {...}
        # ```
        # ----------------------------------------------------

        if response.startswith("```json"):

            response = response[
                len("```json"):
            ].strip()

        elif response.startswith("```"):

            response = response[
                len("```"):
            ].strip()

        if response.endswith("```"):

            response = response[
                :-len("```")
            ].strip()

        return response