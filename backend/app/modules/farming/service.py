from datetime import timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.activity.models import (
    Activity,
    ActivitySource,
    ActivityStatus,
    ActivityType,
)
from app.modules.activity.repository import (
    ActivityRepository,
)

from app.modules.ai_engine.planner import (
    CropPlanner,
)

from app.modules.crop_planner.schemas import (
    CropPlanResponse,
)

from app.modules.crop_season.models import (
    CropSeason,
    CropSeasonStatus,
)
from app.modules.crop_season.repository import (
    CropSeasonRepository,
)

from app.modules.crop_stage.models import (
    CropStage,
    CropStageStatus,
)
from app.modules.crop_stage.repository import (
    CropStageRepository,
)

from app.modules.farm.repository import (
    FarmRepository,
)

from app.modules.farming.schemas import (
    GenerateFarmingPlanRequest,
    GenerateFarmingPlanResponse,
    PlanActivity,
    PlanStage,
    StartFarmingRequest,
    StartFarmingResponse,
)

from app.shared.exceptions import (
    FarmNotFoundError,
    ValidationError,
)


class FarmingService:

    def __init__(
        self,
        db: Session,
        planner: CropPlanner | None = None,
    ):
        self.db = db

        self.farm_repository = FarmRepository(
            db,
        )

        self.crop_repository = CropSeasonRepository(
            db,
        )

        self.stage_repository = CropStageRepository(
            db,
        )

        self.activity_repository = ActivityRepository(
            db,
        )

        self.crop_planner = planner or CropPlanner()

    # ========================================================
    # FARM LOOKUP
    # ========================================================

    def _get_owned_farm(
        self,
        farm_id: UUID,
        farmer_id: UUID,
        land_area: float,
        for_update: bool = False,
    ):
        if for_update:
            farm = (
                self.farm_repository
                .get_by_id_and_farmer_for_update(
                    farm_id=farm_id,
                    farmer_id=farmer_id,
                )
            )
        else:
            farm = self.farm_repository.get_by_id_and_farmer(
                farm_id=farm_id,
                farmer_id=farmer_id,
            )

        if farm is None:
            raise FarmNotFoundError()

        if land_area > farm.land_area:
            raise ValidationError(
                "Crop area cannot exceed farm area.",
            )

        return farm

    # ========================================================
    # GENERATE PLAN
    # ========================================================

    async def generate_plan(
        self,
        request: GenerateFarmingPlanRequest,
        farmer_id: UUID,
    ) -> GenerateFarmingPlanResponse:

        farm = self._get_owned_farm(
            farm_id=request.farm_id,
            farmer_id=farmer_id,
            land_area=request.land_area,
        )

        plan = await self.crop_planner.generate(
            crop_name=request.crop_name,
            crop_variety=request.crop_variety,
            season=request.season.value,
            state=farm.state,
            district=farm.district,
            village=farm.village,
            land_area=request.land_area,
            land_unit=request.land_unit,
            soil_type=farm.soil_type,
        )

        self._validate_generated_plan(
            plan=plan,
            request=request,
        )

        stages = []

        for stage in plan.stages:

            activities = []

            for activity in stage.activities:

                activities.append(
                    PlanActivity(
                        day=activity.day,
                        title=activity.title,
                        activity_type=activity.activity_type,
                        description=activity.description,
                        priority=activity.priority.value,
                        estimated_duration_minutes=(
                            activity.estimated_duration_minutes
                        ),
                    )
                )

            stages.append(
                PlanStage(
                    name=stage.name,
                    description=stage.description,
                    stage_order=stage.stage_order,
                    start_day=stage.start_day,
                    end_day=stage.end_day,
                    activities=activities,
                )
            )

        return GenerateFarmingPlanResponse(
            crop_name=plan.crop_name,
            crop_variety=plan.crop_variety,
            season=request.season,
            sowing_date=request.sowing_date,
            estimated_duration_days=(
                plan.estimated_duration_days
            ),
            stages=stages,
        )

    # ========================================================
    # VALIDATE GENERATED PLAN
    # ========================================================

    @staticmethod
    def _validate_generated_plan(
        plan: CropPlanResponse,
        request: GenerateFarmingPlanRequest,
    ) -> None:

        if (
            plan.crop_name.strip().lower()
            != request.crop_name.strip().lower()
        ):
            raise ValidationError(
                "AI returned a plan for a different crop.",
            )

        if (
            plan.season.strip().upper()
            != request.season.value.upper()
        ):
            raise ValidationError(
                "AI returned a plan for a different season.",
            )

        if (
            request.crop_variety
            and plan.crop_variety
            and plan.crop_variety.strip().lower()
            != request.crop_variety.strip().lower()
        ):
            raise ValidationError(
                "AI returned a plan for a different crop variety.",
            )

    # ========================================================
    # VALIDATE START REQUEST
    # ========================================================

    @staticmethod
    def _validate_start_request(
        request: StartFarmingRequest,
    ) -> int:

        if not request.stages:
            raise ValidationError(
                "At least one crop stage is required.",
            )

        stage_orders = [
            stage.stage_order
            for stage in request.stages
        ]

        expected_orders = list(
            range(
                1,
                len(stage_orders) + 1,
            )
        )

        if sorted(stage_orders) != expected_orders:
            raise ValidationError(
                "Crop stage orders must be unique and "
                "sequential starting from 1.",
            )

        duration_days = 0

        for stage in request.stages:

            if stage.start_day < 1:
                raise ValidationError(
                    f"Invalid start day for stage '{stage.name}'.",
                )

            if stage.end_day < stage.start_day:
                raise ValidationError(
                    f"Invalid timeline for stage '{stage.name}'.",
                )

            if not stage.activities:
                raise ValidationError(
                    f"Stage '{stage.name}' has no activities.",
                )

            for activity in stage.activities:

                if (
                    activity.day < stage.start_day
                    or activity.day > stage.end_day
                ):
                    raise ValidationError(
                        f"Activity '{activity.title}' is outside "
                        f"stage '{stage.name}'.",
                    )

                if activity.estimated_duration_minutes < 1:
                    raise ValidationError(
                        f"Invalid duration for activity "
                        f"'{activity.title}'.",
                    )

                if activity.priority.strip().upper() not in {
                    "HIGH",
                    "MEDIUM",
                    "LOW",
                }:
                    raise ValidationError(
                        f"Invalid priority for activity "
                        f"'{activity.title}'.",
                    )

            duration_days = max(
                duration_days,
                stage.end_day,
            )

        return duration_days

    # ========================================================
    # START FARMING
    # ========================================================

    async def start_farming(
        self,
        request: StartFarmingRequest,
        farmer_id: UUID,
    ) -> StartFarmingResponse:

        duration_days = self._validate_start_request(
            request,
        )

        farm = self._get_owned_farm(
            farm_id=request.farm_id,
            farmer_id=farmer_id,
            land_area=request.land_area,
            for_update=True,
        )

        active_crop = self.crop_repository.get_active_by_farm(
            farm.id,
        )

        if active_crop is not None:
            raise ValidationError(
                "Another crop season is already active "
                "for this farm. Complete or cancel it first.",
            )

        try:

            # ------------------------------------------------
            # Create CropSeason
            # ------------------------------------------------

            crop_season = CropSeason(
                farm_id=farm.id,
                crop_name=request.crop_name,
                crop_variety=request.crop_variety,
                season=request.season,
                year=request.sowing_date.year,
                sowing_date=request.sowing_date,
                expected_harvest_date=(
                    request.sowing_date
                    + timedelta(days=duration_days - 1)
                ),
                land_area=request.land_area,
                land_unit=request.land_unit,
                status=CropSeasonStatus.ACTIVE,
                is_active=True,
            )

            self.crop_repository.create_without_commit(
                crop_season,
            )

            total_activities = 0

            # ------------------------------------------------
            # Create Stages
            # ------------------------------------------------

            for stage_data in request.stages:

                stage = CropStage(
                    crop_season_id=crop_season.id,
                    name=stage_data.name,
                    description=stage_data.description,
                    stage_order=stage_data.stage_order,
                    start_day=stage_data.start_day,
                    end_day=stage_data.end_day,
                    status=(
                        CropStageStatus.ACTIVE
                        if stage_data.stage_order == 1
                        else CropStageStatus.PENDING
                    ),
                    started_at=(
                        request.sowing_date
                        if stage_data.stage_order == 1
                        else None
                    ),
                )

                self.stage_repository.create_without_commit(
                    stage,
                )

                # --------------------------------------------
                # Create Activities
                # --------------------------------------------

                for activity_data in stage_data.activities:

                    try:
                        activity_type = ActivityType(
                            activity_data.activity_type,
                        )

                    except ValueError:
                        activity_type = ActivityType.OTHER

                    scheduled_date = (
                        request.sowing_date
                        + timedelta(
                            days=activity_data.day - 1,
                        )
                    )

                    activity = Activity(
                        crop_season_id=crop_season.id,
                        stage_id=stage.id,
                        activity_type=activity_type,
                        title=activity_data.title,
                        description=activity_data.description,
                        scheduled_date=scheduled_date,
                        original_scheduled_date=scheduled_date,
                        status=ActivityStatus.PENDING,
                        priority=activity_data.priority.strip().upper(),
                        estimated_duration_minutes=(
                            activity_data.estimated_duration_minutes
                        ),
                        source=ActivitySource.AI_PLANNED,
                    )

                    self.activity_repository.create_without_commit(
                        activity,
                    )

                    total_activities += 1

            # ------------------------------------------------
            # Commit everything together
            # ------------------------------------------------

            self.db.commit()

        except Exception:

            self.db.rollback()

            raise

        self.db.refresh(
            crop_season,
        )

        return StartFarmingResponse(
            crop_season_id=crop_season.id,
            crop_name=crop_season.crop_name,
            crop_variety=crop_season.crop_variety,
            season=crop_season.season,
            sowing_date=crop_season.sowing_date,
            estimated_duration_days=duration_days,
            total_stages=len(
                request.stages,
            ),
            total_activities=total_activities,
            message="Farming started successfully.",
        )