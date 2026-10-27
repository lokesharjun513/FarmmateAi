from pydantic import BaseModel, ConfigDict


# ============================================================
# FARMER
# ============================================================


class FarmerCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    preferred_language: str | None = None


# ============================================================
# FARM
# ============================================================


class FarmCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str

    farm_name: str

    village: str
    mandal: str
    district: str
    state: str

    soil_type: str | None = None

    water_source: str | None = None
    water_availability: str | None = None
    irrigation_method: str | None = None

    land_area: float
    land_unit: str


# ============================================================
# CROP STAGE
# ============================================================


class CropStageCard(BaseModel):
    """
    Represents the actual crop-stage lifecycle state.

    This comes from CropStage and is NOT calculated
    by the mobile application.
    """

    id: str

    name: str

    description: str | None = None

    stage_order: int

    start_day: int

    end_day: int

    status: str

    started_at: str | None = None

    completed_at: str | None = None


# ============================================================
# ACTIVE CROP
# ============================================================


class CropCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str

    crop_name: str

    crop_variety: str | None = None

    season: str

    year: int

    status: str

    is_active: bool

    sowing_date: str

    expected_harvest_date: str | None = None

    harvested_date: str | None = None

    land_area: float

    land_unit: str

    crop_age_days: int

    estimated_duration_days: int

    progress_percentage: int

    current_stage: CropStageCard | None = None

    next_stage: CropStageCard | None = None


# ============================================================
# WEATHER
# ============================================================


class WeatherCard(BaseModel):
    temperature: float

    humidity: int

    condition: str

    rain_probability: int | None = None

    is_available: bool = True


# ============================================================
# ADVISOR
# ============================================================


class AdvisorCard(BaseModel):
    summary: str

    priority: str

    available: bool = True


# ============================================================
# ACTIVITY
# ============================================================


class ActivityItem(BaseModel):
    id: str

    title: str

    description: str | None = None

    activity_type: str

    priority: str

    status: str

    scheduled_date: str

    completed_date: str | None = None

    source: str | None = None


# ============================================================
# ASK FARMATE
# ============================================================


class AskFMCard(BaseModel):
    active_session: bool


# ============================================================
# DASHBOARD STATISTICS
# ============================================================


class DashboardStats(BaseModel):

    total_tasks: int

    pending_tasks: int

    in_progress_tasks: int

    completed_tasks: int

    skipped_tasks: int

    today_tasks: int

    today_completed_tasks: int

    today_pending_tasks: int

    today_in_progress_tasks: int


# ============================================================
# DASHBOARD RESPONSE
# ============================================================


class DashboardResponse(BaseModel):

    greeting: str

    farmer: FarmerCard

    farm: FarmCard | None = None

    active_crop: CropCard | None = None

    weather: WeatherCard

    advisor: AdvisorCard

    stats: DashboardStats

    activities: list[ActivityItem]

    ask_fm: AskFMCard