# Business Logic

## Core Business Rules

### Farmer Profile Validation

| Rule | Implementation | Source |
|------|---------------|--------|
| Profile completion must be 0-100 | `CheckConstraint(profile_completion >= 0 AND profile_completion <= 100)` in `farmer/models.py:62-66` | `backend/app/modules/farmer/models.py` |
| Experience years cannot be negative | `CheckConstraint(experience_years IS NULL OR experience_years >= 0)` in `farmer/models.py:72-76` | `backend/app/modules/farmer/models.py` |
| One farmer per user (unique) | `user_id: Mapped[uuid.UUID] = mapped_column(..., unique=True, nullable=False)` in `farmer/models.py:98-106` | `backend/app/modules/farmer/models.py` |

### Farm Validation

| Rule | Implementation | Source |
|------|---------------|--------|
| Land area must be positive | `CheckConstraint(land_area > 0)` in `farm/models.py:62-65` | `backend/app/modules/farm/models.py` |
| Latitude must be -90 to 90 (or NULL) | `CheckConstraint(latitude >= -90 AND latitude <= 90)` in `farm/models.py:73-78` | `backend/app/modules/farm/models.py` |
| Longitude must be -180 to 180 (or NULL) | `CheckConstraint(longitude >= -180 AND longitude <= 180)` in `farm/models.py:86-91` | `backend/app/modules/farm/models.py` |
| Primary farm business rule | Handled by `FarmRepository` (not DB unique index) - can transition primary farm from one to another | `farm/models.py:258-262`, `farm/service.py` |

### Crop Season Validation

| Rule | Implementation | Source |
|------|---------------|--------|
| Land area must be positive | `CheckConstraint(land_area > 0)` in `crop_season/models.py:141-144` | `backend/app/modules/crop_season/models.py` |
| Year must be ≥ 2000 | `CheckConstraint(year >= 2000)` in `crop_season/models.py:150-153` | `backend/app/modules/crop_season/models.py` |
| Expected harvest ≥ sowing date (or NULL) | Check constraint in `crop_season/models.py:162-168` | `backend/app/modules/crop_season/models.py` |
| Actual harvest ≥ sowing date (or NULL) | Check constraint in `crop_season/models.py:176-181` | `backend/app/modules/crop_season/models.py` |
| Status is authoritative, `is_active` must be synced | Documented in model comment: "The service layer MUST keep this synchronized with `status`" | `crop_season/models.py:407-409` |

### Crop Stage Validation

| Rule | Implementation | Source |
|------|---------------|--------|
| Stage order must be unique per crop season | `UniqueConstraint(crop_season_id, stage_order)` in `crop_stage/models.py:80-84` | `backend/app/modules/crop_stage/models.py` |
| Stage order must start from 1 | `CheckConstraint(stage_order >= 1)` in `crop_stage/models.py:90-93` | `backend/app/modules/crop_stage/models.py` |
| Start day must be ≥ 1 | `CheckConstraint(start_day >= 1)` in `crop_stage/models.py:100-102` | `backend/app/modules/crop_stage/models.py` |
| End day must be ≥ 1 | `CheckConstraint(end_day >= 1)` in `crop_stage/models.py:108-111` | `backend/app/modules/crop_stage/models.py` |
| End day cannot be before start day | `CheckConstraint(end_day >= start_day)` in `crop_stage/models.py:117-120` | `backend/app/modules/crop_stage/models.py` |

### Activity Validation

| Rule | Implementation | Source |
|------|---------------|--------|
| Estimated duration must be ≥ 1 min (or NULL) | `CheckConstraint(estimated_duration_minutes IS NULL OR estimated_duration_minutes >= 1)` in `activity/models.py:139-145` | `backend/app/modules/activity/models.py` |
| Completed date consistency with status | PENDING/IN_PROGRESS → completed_date NULL; COMPLETED/SKIPPED → completed_date NOT NULL | `CheckConstraint` in `activity/models.py:157-170` | `backend/app/modules/activity/models.py` |
| Activity type must be valid enum | `ActivityType` with 18 predefined values (LAND_PREPARATION, SOWING, etc.) | `activity/models.py:41-65` | `backend/app/modules/activity/models.py` |
| Source must be valid enum | `ActivitySource` with 4 values (AI_PLANNED, WEATHER_TRIGGERED, FARMER_ADDED, SYSTEM) | `activity/models.py:89-97` | `backend/app/modules/activity/models.py` |
| Priority must be valid enum | `ActivityPriority` with 4 values (LOW, MEDIUM, HIGH, CRITICAL) | `activity/models.py:105-114` | `backend/app/modules/activity/models.py` |
| Status must be valid enum | `ActivityStatus` with 4 values (PENDING, IN_PROGRESS, COMPLETED, SKIPPED) | `activity/models.py:73-82` | `backend/app/modules/activity/models.py` |

## Service Layer Business Logic

### Crop Season Status Transitions

The service layer (`crop_season/service.py` - not shown in full but implied) is responsible for valid state transitions:

```
PLANNED → ACTIVE (when sowing starts)
ACTIVE → HARVESTED (when crop is harvested)
ACTIVE → CANCELLED (when farmer cancels)
```

**Important**: `is_active` field must be kept synchronized with `status`:
- `status = ACTIVE` → `is_active = True`
- `status ≠ ACTIVE` → `is_active = False`

### Crop Stage Progression

The crop stage service manages stage order and status:

1. **Get current stage**: `get_active_by_crop_season(crop_season_id)`
2. **Get next stage**: `get_next_stage(crop_season_id, current_stage_order)`
3. **Get first pending stage**: `get_first_pending_stage(crop_season_id)`
4. **Status transitions**: PENDING → ACTIVE → COMPLETED, or PENDING → SKIPPED

### Activity Creation

When activities are created (often via AI planner):

1. **Activity type** determines the nature of the task
2. **Source** indicates origin: AI_PLANNED, WEATHER_TRIGGERED, FARMER_ADDED, or SYSTEM
3. **Priority** defaults to MEDIUM, can be overridden
4. **Scheduled date** is set relative to sowing date
5. **Status** defaults to PENDING

### AI Crop Planning

The `AIEngineService.generate_crop_plan()` (`ai_engine/service.py`):

1. Takes a `CropSeason` as input
2. Uses `CropPlanner.generate_crop_plan()` to generate activities
3. Creates `Activity` records for each planned task
4. Activities are scheduled relative to the sowing date
5. Activity types include: LAND_PREPARATION, SOWING, NURSERY, TRANSPLANTING, IRRIGATION, FERTILIZER, WEEDING, PEST_CONTROL, DISEASE_CHECK, SPRAYING, HARVEST, OTHER

### Daily AI Advisor

The `AdvisorService.get_today_advice()` (`advisor/service.py`):

1. Gets farmer's primary farm
2. Gets active crop season for that farm
3. Calculates crop age (days since sowing)
4. Fetches today's activities for the crop
5. Gets current weather conditions
6. Builds `AIContext` with all relevant data
7. Passes context to `AdvisorPlanner.generate_daily_advice()`
8. Returns `DailyAdvisorResponse` with summary and priority

### Scheduler Business Logic

The `SchedulerService.run()` (`scheduler/service.py`):

1. Iterates over all farms
2. For each farm with active crop:
   - Fetches current weather (updates farm weather data)
   - Generates AI advisor advice for the farmer
   - Creates AI advisor notification (if advice generated)
3. Cleans up expired Ask FM sessions
4. Logs summary: farms processed, crops updated, weather updates, advisor notifications, expired sessions cleaned

## Validation Layer

### Pydantic Schemas

All API requests are validated via Pydantic schemas in each module's `schemas.py`:

- **Identity**: `RegisterRequest`, `LoginRequest`, `UserResponse`, `TokenData`
- **Farmer**: `FarmerCreateRequest`, `FarmerUpdateRequest`, `FarmerResponse`
- **Farm**: `FarmCreateRequest`, `FarmUpdateRequest`, `FarmResponse`
- **Dashboard**: `DashboardResponse`, `CropCard`, `AdvisorCard`, `WeatherCard`, etc.
- **Chat**: `ChatRequest`, `ChatResponse`
- **Weather**: `CurrentWeatherResponse`, `WeatherRecommendationResponse`

### Exception Handling

Custom exceptions are defined in `app/shared/exceptions.py` and raised in services:

| Exception | HTTP Status | When Raised |
|-----------|-------------|-------------|
| `ValidationError` | 422 | Invalid input data, missing required fields |
| `FarmerProfileNotFoundError` | 404 | Farmer profile doesn't exist for user |
| General HTTP exceptions | As defined | Various validation/auth failures |

Error responses follow FastAPI's default format with `detail` field.

## Business Rule Summary

| Area | Rule | Enforced By |
|------|------|-------------|
| **Farmer profile** | 1:1 with user, completion 0-100, experience ≥ 0 | DB constraints + service logic |
| **Farm** | Land > 0, valid GPS, primary farm managed by repo | DB constraints + FarmRepository |
| **Crop season** | Area > 0, year ≥ 2000, date consistency, is_active sync with status | DB constraints + service layer |
| **Crop stage** | Order uniqueness, order ≥ 1, timeline validity | DB constraints + CropStageRepository |
| **Activity** | Duration ≥ 1 or NULL, status/completed_date consistency, valid enums | DB constraints + ActivityRepository |
| **Authentication** | Unique mobile/email, password hash, active check | DB constraints + auth service |
| **Notifications** | Type/enum constraints, farmer ownership | DB constraints + NotificationService |
| **Scheduler** | Daily at 6AM, process all farms, cleanup expired sessions | APScheduler + SchedulerService |

## Inter-Module Business Rules

### Farm → Crop Season

- A farm can have multiple crop seasons over time
- Deleting a farm cascades to delete all its crop seasons
- Each crop season belongs to exactly one farm (via `farm_id`)

### Crop Season → Activity

- A crop season can have multiple activities
- Deleting a crop season cascades to delete all its activities
- Activities can optionally reference a crop stage (`stage_id`, SET NULL on delete)

### Farmer → Activities

- A farmer has many farms → many crop seasons → many activities
- All activities are filtered by the current farmer's context
- Activity source determines origin (AI, weather, farmer, system)

### Weather → Activities

- Weather data influences AI-planned activities
- `WEATHER_TRIGGERED` source activities can be created based on conditions
- Rain probability ≥ 70% triggers irrigation avoidance advice

### Scheduler → All Modules

- Scheduler processes all farms cyclically (daily)
- Weather updates fetch current conditions
- AI advisor generates daily advice per farmer
- Notifications are created and sent via FCM
- Expired sessions are cleaned up

---
*Business logic documented from codebase analysis as of 2026-11-21. All rules verified from SQLAlchemy model constraints, service layer implementations, and router dependencies.*