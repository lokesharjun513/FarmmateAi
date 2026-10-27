from datetime import timedelta

from sqlalchemy.exc import IntegrityError

from app.modules.ai_engine.planner import (
    CropPlanner,
)

from app.modules.activity.models import (
    Activity,
    ActivitySource,
    ActivityStatus,
    ActivityType,
)

from app.modules.crop_season.models import (
    CropSeason,
    CropSeasonStatus,
)

from app.modules.crop_stage.models import (
    CropStage,
    CropStageStatus,
)

from app.modules.crop_planner.repository import (
    CropPlannerRepository,
)

from app.modules.crop_planner.schemas import (
    CropPlanResponse,
)

from app.shared.exceptions import (
    ValidationError,
)


class CropPlannerService:

    MAX_PLAN_GENERATION_ATTEMPTS = 2

    def __init__(
        self,
        repository: CropPlannerRepository,
    ):

        self.repository = repository

        self.planner = CropPlanner()

    # ========================================================
    # GENERATE AND SAVE CROP PLAN
    # ========================================================

    async def generate_plan(
        self,
        *,
        crop_season: CropSeason,
        state: str,
        district: str,
        village: str,
        soil_type: str | None,
    ) -> CropPlanResponse:

        # ----------------------------------------------------
        # Crop must be planned.
        # ----------------------------------------------------

        if (
            crop_season.status
            != CropSeasonStatus.PLANNED
        ):

            raise ValidationError(
                "Crop plan can only be generated "
                "for a planned crop season."
            )

        # ----------------------------------------------------
        # Prevent duplicate plans.
        # ----------------------------------------------------

        if self.repository.has_plan(
            crop_season.id,
        ):

            raise ValidationError(
                "A crop plan already exists for "
                "this crop season."
            )

        # ----------------------------------------------------
        # Generate and validate AI plan.
        #
        # A bounded retry handles occasional model drift while
        # keeping the saved crop season as the canonical record.
        # ----------------------------------------------------

        last_error: ValidationError | None = None

        for attempt in range(
            1,
            self.MAX_PLAN_GENERATION_ATTEMPTS + 1,
        ):

            try:

                plan = await self.planner.generate(
                    crop_name=crop_season.crop_name,
                    crop_variety=crop_season.crop_variety,
                    season=crop_season.season.value,
                    state=state,
                    district=district,
                    village=village,
                    land_area=crop_season.land_area,
                    land_unit=crop_season.land_unit,
                    soil_type=soil_type,
                )

                self._validate_plan(
                    plan=plan,
                    crop_season=crop_season,
                )

            except ValidationError as exc:

                last_error = exc

                if attempt < self.MAX_PLAN_GENERATION_ATTEMPTS:
                    continue

                raise ValidationError(
                    "AI could not produce a valid crop plan after "
                    f"{self.MAX_PLAN_GENERATION_ATTEMPTS} attempts. "
                    f"{exc}"
                ) from exc

            # Preserve the farmer's saved values in the response.
            plan.crop_name = crop_season.crop_name
            plan.crop_variety = crop_season.crop_variety

            break

        else:

            raise last_error or ValidationError(
                "AI could not produce a valid crop plan."
            )

        # ----------------------------------------------------
        # Serialize persistence and re-check for a plan that
        # may have been saved by a concurrent request while
        # the AI was generating this one.
        # ----------------------------------------------------

        self.repository.lock_crop_season(
            crop_season.id,
        )

        if self.repository.has_plan(
            crop_season.id,
        ):

            raise ValidationError(
                "A crop plan already exists for "
                "this crop season."
            )

        # ----------------------------------------------------
        # Save everything inside one transaction.
        # ----------------------------------------------------

        try:

            self._save_plan(
                plan=plan,
                crop_season=crop_season,
            )

            self.repository.commit()

        except IntegrityError as exc:

            self.repository.rollback()

            if self.repository.has_plan(
                crop_season.id,
            ):

                raise ValidationError(
                    "A crop plan already exists for "
                    "this crop season."
                ) from exc

            raise

        except Exception:

            self.repository.rollback()

            raise

        return plan

    # ========================================================
    # VALIDATE PLAN
    # ========================================================

    def _validate_plan(
        self,
        *,
        plan: CropPlanResponse,
        crop_season: CropSeason,
    ) -> None:

        # ----------------------------------------------------
        # Crop name
        # ----------------------------------------------------

        if (
            plan.crop_name.strip().lower()
            != crop_season.crop_name.strip().lower()
        ):

            raise ValidationError(
                "AI returned a plan for a different crop."
            )

        # ----------------------------------------------------
        # Crop variety
        # ----------------------------------------------------

        expected_variety = (
            crop_season.crop_variety or ""
        ).strip().lower()

        returned_variety = (
            plan.crop_variety or ""
        ).strip().lower()

        if returned_variety != expected_variety:

            raise ValidationError(
                "AI returned a plan for a different "
                "crop variety."
            )

        # ----------------------------------------------------
        # Season
        # ----------------------------------------------------

        if (
            plan.season.strip().upper()
            != crop_season.season.value.upper()
        ):

            raise ValidationError(
                "AI returned a plan for a different "
                "farming season."
            )

        # ----------------------------------------------------
        # Duration
        # ----------------------------------------------------

        if plan.estimated_duration_days < 1:

            raise ValidationError(
                "AI returned an invalid crop duration."
            )

        # ----------------------------------------------------
        # Stages
        # ----------------------------------------------------

        if not plan.stages:

            raise ValidationError(
                "AI returned a crop plan without stages."
            )

        stage_orders = [
            stage.stage_order
            for stage in plan.stages
        ]

        if len(stage_orders) != len(
            set(stage_orders)
        ):

            raise ValidationError(
                "AI returned duplicate crop stage orders."
            )

        expected_orders = list(
            range(
                1,
                len(stage_orders) + 1,
            )
        )

        if sorted(stage_orders) != expected_orders:

            raise ValidationError(
                "Crop stage orders must be sequential "
                "starting from 1."
            )

        # ----------------------------------------------------
        # Validate stages
        # ----------------------------------------------------

        for stage in plan.stages:

            if stage.start_day < 1:

                raise ValidationError(
                    f"Invalid start day for stage "
                    f"'{stage.name}'."
                )

            if stage.end_day < stage.start_day:

                raise ValidationError(
                    f"Invalid timeline for stage "
                    f"'{stage.name}'."
                )

            if (
                stage.end_day
                > plan.estimated_duration_days
            ):

                raise ValidationError(
                    f"Stage '{stage.name}' extends "
                    "beyond crop duration."
                )

            if not stage.activities:

                raise ValidationError(
                    f"Stage '{stage.name}' has no activities."
                )

            # ------------------------------------------------
            # Validate activities
            # ------------------------------------------------

            for activity in stage.activities:

                if (
                    activity.day < stage.start_day
                    or activity.day > stage.end_day
                ):

                    raise ValidationError(
                        f"Activity '{activity.title}' "
                        "is outside its stage timeline."
                    )

                try:

                    ActivityType(
                        activity.activity_type.upper()
                    )

                except ValueError as exc:

                    raise ValidationError(
                        f"Invalid activity type: "
                        f"{activity.activity_type}"
                    ) from exc

    # ========================================================
    # SAVE PLAN
    # ========================================================

    def _save_plan(
        self,
        *,
        plan: CropPlanResponse,
        crop_season: CropSeason,
    ) -> tuple[int, int]:

        stages_created = 0
        activities_created = 0

        # ----------------------------------------------------
        # Always save stages in correct order.
        # ----------------------------------------------------

        sorted_stages = sorted(
            plan.stages,
            key=lambda stage: stage.stage_order,
        )

        for ai_stage in sorted_stages:

            # ------------------------------------------------
            # Create CropStage
            # ------------------------------------------------

            stage = CropStage(
                crop_season_id=crop_season.id,
                name=ai_stage.name,
                description=ai_stage.description,
                stage_order=ai_stage.stage_order,
                start_day=ai_stage.start_day,
                end_day=ai_stage.end_day,
                status=CropStageStatus.PENDING,
            )

            stage = self.repository.create_stage(
                stage,
            )

            stages_created += 1

            # ------------------------------------------------
            # Create activities
            # ------------------------------------------------

            activities: list[Activity] = []

            for ai_activity in ai_stage.activities:

                activity_type = ActivityType(
                    ai_activity.activity_type.upper()
                )

                scheduled_date = (
                    crop_season.sowing_date
                    + timedelta(
                        days=ai_activity.day - 1,
                    )
                )

                activity = Activity(
                    crop_season_id=crop_season.id,

                    stage_id=stage.id,

                    activity_type=activity_type,

                    title=ai_activity.title,

                    description=ai_activity.description,

                    scheduled_date=scheduled_date,

                    original_scheduled_date=None,

                    completed_date=None,

                    status=ActivityStatus.PENDING,

                    notes=None,

                    priority=(
                        ai_activity.priority.value
                    ),

                    estimated_duration_minutes=(
                        ai_activity
                        .estimated_duration_minutes
                    ),

                    source=ActivitySource.AI_PLANNED,
                )

                activities.append(
                    activity,
                )

            if activities:

                self.repository.create_activities(
                    activities,
                )

                activities_created += len(
                    activities
                )

        return (
            stages_created,
            activities_created,
        )