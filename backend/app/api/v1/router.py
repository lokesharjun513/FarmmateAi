from fastapi import APIRouter


# ============================================================
# MODULE ROUTERS
# ============================================================

from app.modules.identity.router import (
    router as auth_router,
)

from app.modules.farmer.router import (
    router as farmer_router,
)

from app.modules.farm.router import (
    router as farm_router,
)

from app.modules.onboarding.router import (
    router as onboarding_router,
)

from app.modules.crop_season.router import (
    router as crop_season_router,
)

from app.modules.crop_stage.router import (
    router as crop_stage_router,
)

from app.modules.activity.router import (
    router as activity_router,
)

from app.modules.crop_planner.router import (
    router as crop_planner_router,
)

from app.modules.dashboard.router import (
    router as dashboard_router,
)

from app.modules.weather.router import (
    router as weather_router,
)

from app.modules.advisor.router import (
    router as advisor_router,
)

from app.modules.chat.router import (
    router as chat_router,
)

from app.modules.notifications.router import (
    router as notifications_router,
)

from app.modules.crop_recommendation.router import (
    router as crop_recommendation_router,
)

from app.modules.farming.router import (
    router as farming_router,
)

from app.modules.scheduler.router import (
    router as scheduler_router,
)

# ============================================================
# API ROUTER
# ============================================================

api_router = APIRouter(
    prefix="/api/v1",
)


# ============================================================
# AUTHENTICATION / FARMER
# ============================================================

api_router.include_router(
    auth_router,
)

api_router.include_router(
    farmer_router,
)

api_router.include_router(
    farm_router,
)

api_router.include_router(
    onboarding_router,
)


# ============================================================
# FARMING CORE
# ============================================================

api_router.include_router(
    crop_season_router,
)

api_router.include_router(
    crop_planner_router,
)

api_router.include_router(
    crop_stage_router,
)

api_router.include_router(
    activity_router,
)


# ============================================================
# FARMER SUPPORT
# ============================================================

api_router.include_router(
    dashboard_router,
)

api_router.include_router(
    weather_router,
)

api_router.include_router(
    advisor_router,
)

api_router.include_router(
    chat_router,
)

api_router.include_router(
    notifications_router,
)


# ============================================================
# AI / RECOMMENDATIONS
# ============================================================

api_router.include_router(
    crop_recommendation_router,
)


# ============================================================
# FARMING AUTOMATION
# ============================================================

api_router.include_router(
    farming_router,
)

api_router.include_router(
    scheduler_router,
)
