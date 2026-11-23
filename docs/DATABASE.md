# Database - PostgreSQL Schema

## Overview

The application uses **PostgreSQL** as the relational database with **SQLAlchemy 2.x** as the ORM. All models follow a consistent pattern with `TimestampMixin` for created/updated tracking.

## Entity Relationship Diagram (ER Diagram)

```mermaid
erDiagram
    %% Core identity
    USER ||--|{ FARMER : "one-to-one"
    USER {
        UUID id PK
        String full_name NOT NULL
        String mobile UNIQUE NOT NULL
        String email UNIQUE NOT NULL
        String password_hash NOT NULL
        Boolean is_active default True
        DateTime created_at
        DateTime updated_at
    }
    
    FARMER {
        UUID id PK
        UUID user_id FK → users.id ON DELETE CASCADE UNIQUE
        String preferred_language default "English"
        Integer experience_years NULLable
        Integer profile_completion default 0
        Boolean onboarding_completed default False
        DateTime created_at
        DateTime updated_at
    }
    
    %% Farm relationships
    FARMER ||--o{ FARM : "one-to-many"
    FARM {
        UUID id PK
        UUID farmer_id FK → farmers.id ON DELETE CASCADE
        String farm_name NOT NULL
        String state NOT NULL
        String district NOT NULL
        String mandal NOT NULL
        String village NOT NULL
        Float latitude NULLable
        Float longitude NULLable
        Float land_area NOT NULL
        String land_unit default "Acres"
        String soil_type NULLable
        String water_source NULLable
        String water_availability NULLable
        String irrigation_method NULLable
        Boolean is_primary default False
        DateTime created_at
        DateTime updated_at
    }
    
    FARM ||--o{ CROP_SEASON : "one-to-many"
    CROP_SEASON {
        UUID id PK
        UUID farm_id FK → farms.id ON DELETE CASCADE
        String crop_name NOT NULL
        String crop_variety NULLable
        Float land_area NOT NULL
        String land_unit default "Acres"
        FarmingSeason season NOT NULL
        Integer year NOT NULL
        Date sowing_date NOT NULL
        Date NULLable expected_harvest_date
        Date NULLable harvested_date
        CropSeasonStatus status default "PLANNED"
        Boolean is_active default False
        String NULLable notes
        String NULLable cancellation_reason
        DateTime created_at
        DateTime updated_at
    }
    
    CROP_SEASON ||--o{ CROP_STAGE : "one-to-many"
    CROP_STAGE {
        UUID id PK
        UUID crop_season_id FK → crop_seasons.id ON DELETE CASCADE
        Integer stage_order NOT NULL
        String name NOT NULL
        Text NULLable description
        Date start_day NOT NULL
        Date end_day NOT NULL
        CropStageStatus status default "PENDING"
        Date NULLable started_at
        Date NULLable completed_at
        Integer NULLable estimated_duration_minutes
        DateTime created_at
        DateTime updated_at
    }
    
    CROP_SEASON ||--o{ ACTIVITY : "one-to-many"
    ACTIVITY {
        UUID id PK
        UUID crop_season_id FK → crop_seasons.id ON DELETE CASCADE
        UUID NULLable stage_id FK → crop_stages.id ON DELETE SET NULL
        ActivityType activity_type NOT NULL
        ActivitySource source default "AI_PLANNED"
        ActivityPriority priority default "MEDIUM"
        ActivityStatus status default "PENDING"
        String title NOT NULL
        Text NULLable description
        Date scheduled_date NOT NULL
        Date NULLable original_scheduled_date
        Date NULLable completed_date
        Integer NULLable estimated_duration_minutes
        String NULLable notes
        DateTime created_at
        DateTime updated_at
    }
    
    %% Chat/FM relationships
    FARMER ||--o{ ASK_FM_SESSION : "one-to-many"
    ASK_FM_SESSION {
        UUID id PK
        UUID farmer_id FK → farmers.id ON DELETE CASCADE
        DateTime created_at
        DateTime updated_at
    }
    
    ASK_FM_SESSION ||--o{ ASK_FM_MESSAGE : "one-to-many"
    ASK_FM_MESSAGE {
        UUID id PK
        UUID session_id FK → ask_fm_sessions.id ON DELETE CASCADE
        String message NOT NULL
        String NULLable ai_response
        DateTime created_at
    }
    
    %% Notification relationships
    FARMER ||--o{ NOTIFICATION : "one-to-many"
    NOTIFICATION {
        UUID id PK
        UUID farmer_id FK → farmers.id ON DELETE CASCADE
        NotificationType type NOT NULL
        NotificationPriority priority NOT NULL
        Boolean is_read default False
        String title NOT NULL
        Text message NOT NULL
        DateTime created_at
    }
    
    FARMER ||--o{ DEVICE_TOKEN : "one-to-many"
    DEVICE_TOKEN {
        UUID id PK
        UUID farmer_id FK → farmers.id ON DELETE CASCADE
        String token NOT NULL
        String platform NOT NULL
        Boolean active default True
        DateTime created_at
    }
```

## Core Models

### `users` table

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | Primary Key | Unique identifier |
| `full_name` | String(100) | NOT NULL | User's full name |
| `mobile` | String(20) | UNIQUE, NOT NULL | Contact number (identity) |
| `email` | String(255) | UNIQUE, NOT NULL | Email address |
| `password_hash` | String(255) | NOT NULL | BCrypt/Argon2 hash |
| `is_active` | Boolean | default True, index | Account status |
| `created_at` | DateTime | - | Auto-created |
| `updated_at` | DateTime | - | Auto-updated |

**Indexes**: `ix_users_mobile`, `ix_users_email`, `ix_users_is_active`

### `farmers` table

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | Primary Key | Unique identifier |
| `user_id` | UUID | FK → users.id, UNIQUE, NOT NULL | Links to User (1:1) |
| `preferred_language` | String(20) | default "English" | UI language preference |
| `experience_years` | Integer | NULLable, ≥ 0 (check) | Farming experience |
| `profile_completion` | Integer | default 0, 0-100 (check) | Onboarding progress % |
| `onboarding_completed` | Boolean | default False, index | Onboarding status |
| `created_at` | DateTime | - | Auto-created |
| `updated_at` | DateTime | - | Auto-updated |

**Constraints**: `ck_farmer_profile_completion_valid`, `ck_farmer_experience_years_valid`
**Indexes**: `ix_farmers_onboarding_completed`

### `farms` table

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | Primary Key | Unique identifier |
| `farmer_id` | UUID | FK → farmers.id, ON DELETE CASCADE, index | Farm owner |
| `farm_name` | String(100) | NOT NULL | Farm name |
| `state` | String(100) | NOT NULL | State/Province |
| `district` | String(100) | NOT NULL | District |
| `mandal` | String(100) | NOT NULL | Mandal/Taluk |
| `village` | String(100) | NOT NULL | Village |
| `latitude` | Float | NULLable | GPS latitude |
| `longitude` | Float | NULLable | GPS longitude |
| `land_area` | Float | NOT NULL, > 0 (check) | Land area |
| `land_unit` | String(20) | default "Acres" | Area unit |
| `soil_type` | String(50) | NULLable | Soil classification |
| `water_source` | String(50) | NULLable | Irrigation source |
| `water_availability` | String(20) | NULLable | LOW/MEDIUM/HIGH/Rain-fed |
| `irrigation_method` | String(30) | NULLable | Drip/Sprinkler/Flood etc. |
| `is_primary` | Boolean | default False | Primary farm flag |
| `created_at` | DateTime | - | Auto-created |
| `updated_at` | DateTime | - | Auto-updated |

**Constraints**: `ck_farm_land_area_positive`, `ck_farm_latitude_valid`, `ck_farm_longitude_valid`
**Indexes**: `ix_farms_farmer_id`, `ix_farms_is_primary`

### `crop_seasons` table

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | Primary Key | Unique identifier |
| `farm_id` | UUID | FK → farms.id, ON DELETE CASCADE, index | Owner farm |
| `crop_name` | String(100) | NOT NULL | Crop variety name |
| `crop_variety` | String(100) | NULLable | Specific variety |
| `land_area` | Float | NOT NULL, > 0 (check) | Allocated area |
| `land_unit` | String(20) | default "Acres" | Area unit |
| `season` | Enum (KHARIF/RABI/ZAID) | NOT NULL | Farming season |
| `year` | Integer | ≥ 2000 (check) | Cultivation year |
| `sowing_date` | Date | NOT Sowing date |
| `expected_harvest_date` | Date | NULLable, ≥ sowing_date (check) | Planned harvest |
| `harvested_date` | Date | NULLable, ≥ sowing_date (check) | Actual harvest |
| `status` | Enum (PLANNED/ACTIVE/HARVESTED/CANCELLED) | default "PLANNED", index | Lifecycle state |
| `is_active` | Boolean | default False, index | Activity flag |
| `notes` | Text | NULLable | Additional notes |
| `cancellation_reason` | Text | NULLable | If cancelled |
| `created_at` | DateTime | - | Auto-created |
| `updated_at` | DateTime | - | Auto-updated |

**Indexes**: `ix_crop_season_farm_status`, `ix_crop_season_farm_year`, `ix_crop_season_farm_season`, `ix_crop_season_sowing_date`, `ix_crop_season_expected_harvest_date`, `ix_crop_season_harvested_date`, `ix_crop_season_status`, `ix_crop_season_is_active`
**Constraints**: `ck_crop_season_land_area_positive`, `ck_crop_season_year_valid`, `ck_crop_season_expected_harvest_valid`, `ck_crop_season_harvested_date_valid`

### `crop_stages` table

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | Primary Key | Unique identifier |
| `crop_season_id` | UUID | FK → crop_seasons.id, ON DELETE CASCADE, index | Parent crop season |
| `name` | String(100) | NOT NULL | Stage name (e.g., "Land Preparation") |
| `description` | Text | NULLable | Stage description |
| `stage_order` | Integer | ≥ 1 (check), Unique(crop_season_id, stage_order) | Stage sequence |
| `start_day` | Integer | ≥ 1 (check) | Start day relative to sowing |
| `end_day` | Integer | ≥ 1, ≥ start_day (check) | End day relative to sowing |
| `status` | Enum (PENDING/ACTIVE/COMPLETED/SKIPPED) | default "PENDING", index | Stage status |
| `started_at` | Date | NULLable | When stage started |
| `completed_at` | Date | NULLable | When stage completed |
| `created_at` | DateTime | - | Auto-created |
| `updated_at` | DateTime | - | Auto-updated |

**Constraints**: `uq_crop_stage_season_order`, `ck_crop_stage_order_positive`, `ck_crop_stage_start_day_positive`, `ck_crop_stage_end_day_positive`, `ck_crop_stage_valid_timeline`
**Indexes**: `ix_crop_stage_season_status`, `ix_crop_stage_season_order`

### `activities` table

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | Primary Key | Unique identifier |
| `crop_season_id` | UUID | FK → crop_seasons.id, ON DELETE CASCADE, index | Parent crop season |
| `stage_id` | UUID | FK → crop_stages.id, ON DELETE SET NULL, NULLable | Optional stage |
| `activity_type` | Enum (18 types) | NOT NULL | Type of activity |
| `title` | String(150) | NOT NULL | Activity title |
| `description` | Text | NULLable | Detailed description |
| `scheduled_date` | Date | NOT NULL, index | Scheduled date |
| `original_scheduled_date` | Date | NULLable | First scheduled date |
| `completed_date` | Date | NULLable, consistency constraint | Actual completion |
| `status` | Enum (PENDING/IN_PROGRESS/COMPLETED/SKIPPED) | default "PENDING", index | Activity status |
| `priority` | Enum (LOW/MEDIUM/HIGH/CRITICAL) | default "MEDIUM", index | Priority level |
| `source` | Enum (AI_PLANNED/WEATHER_TRIGGERED/FARMER_ADDED/SYSTEM) | default "AI_PLANNED", index | Origin source |
| `notes` | Text | NULLable | Additional notes |
| `estimated_duration_minutes` | Integer | NULLable, ≥ 1 (check) | Estimated time |
| `created_at` | DateTime | - | Auto-created |
| `updated_at` | DateTime | - | Auto-updated |

**Constraints**: `ck_activity_duration_positive`, `ck_activity_completed_date_consistency`
**Indexes**: `ix_activity_crop_date_status`, `ix_activity_stage_date`, `ix_activity_crop_status_priority`, `ix_activity_crop_source`, `ix_activity_date_priority`, `ix_activity_crop_completed_date`, `ix_activity_crop_stage_status`

### `ask_fm_sessions` table

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | Primary Key | Unique identifier |
| `farmer_id` | UUID | FK → farmers.id, ON DELETE CASCADE | Farmer owner |
| `created_at` | DateTime | - | Auto-created |
| `updated_at` | DateTime | - | Auto-updated |

### `ask_fm_messages` table

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | Primary Key | Unique identifier |
| `session_id` | UUID | FK → ask_fm_sessions.id, ON DELETE CASCADE | Parent session |
| `message` | Text | NOT NULL | User/AI message |
| `ai_response` | Text | NULLAI response from FarmMate |
| `created_at` | DateTime | - | Auto-created |

### `notifications` table

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | Primary Key | Unique identifier |
| `farmer_id` | UUID | FK → farmers.id, ON DELETE CASCADE | Recipient |
| `type` | Enum (NotificationType) | NOT NULL | Notification category |
| `priority` | Enum (NotificationPriority) | NOT NULL | Importance level |
| `is_read` | Boolean | default False | Read status |
| `title` | String | NOT NULL | Notification title |
| `message` | Text | NOT NULL | Notification body |
| `created_at` | DateTime | - | Auto-created |

**Enumerations**:
- `NotificationType`: AI_ADVISOR, WEATHER_UPDATE, ACTIVITY_REMINDER, SYSTEM
- `NotificationPriority`: LOW, MEDIUM, HIGH

**Indexes**: `ix_notifications_farmer_id`, `ix_notifications_type`, `ix_notifications_is_read`

### `device_tokens` table

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | Primary Key | Unique identifier |
| `farmer_id` | UUID | FK → farmers.id, ON DELETE CASCADE | Owner farmer |
| `token` | String | NOT FCM registration token |
| `platform` | String | NOT iOS/Android/Web |
| `active` | Boolean | default True | Token active status |
| `created_at` | DateTime | - | Auto-created |

## Relationship Summary

```
User (1)──(1) Farmer
Farmer (1)──(m) Farm
Farm (1)──(m) CropSeason
CropSeason (1)──(m) CropStage
CropSeason (1)──(m) Activity
Farmer (1)──(m) AskFMSession
AskFMSession (1)──(m) AskFMMessage
Farmer (1)──(m) Notification
Farmer (1)──(m) DeviceToken
```

## Constraints Overview

| Table | Constraint Name | Description |
|-------|----------------|-------------|
| farmers | `ck_farmer_profile_completion_valid` | profile_completion must be 0-100 |
| farmers | `ck_farmer_experience_years_valid` | experience_years ≥ 0 or NULL |
| farms | `ck_farm_land_area_positive` | land_area > 0 |
| farms | `ck_farm_latitude_valid` | latitude ∈ [-90, 90] or NULL |
| farms | `ck_farm_longitude_valid` | longitude ∈ [-180, 180] or NULL |
| crop_seasons | `ck_crop_season_land_area_positive` | land_area > 0 |
| crop_seasons | `ck_crop_season_year_valid` | year ≥ 2000 |
| crop_seasons | `ck_crop_season_expected_harvest_valid` | expected_harvest_date ≥ sowing_date or NULL |
| crop_seasons | `ck_crop_season_harvested_date_valid` | harvested_date ≥ sowing_date or NULL |
| crop_stages | `uq_crop_stage_season_order` | Unique (crop_season_id, stage_order) |
| crop_stages | `ck_crop_stage_order_positive` | stage_order ≥ 1 |
| crop_stages | `ck_crop_stage_start_day_positive` | start_day ≥ 1 |
| crop_stages | `ck_crop_stage_end_day_positive` | end_day ≥ 1 |
| crop_stages | `ck_crop_stage_valid_timeline` | end_day ≥ start_day |
| activities | `ck_activity_duration_positive` | estimated_duration_minutes ≥ 1 or NULL |
| activities | `ck_activity_completed_date_consistency` | Status/completed_date consistency |
| users | (implicit) | Unique mobile, Unique email |

## Data Access Patterns

### Common Query Patterns

1. **Get active crop for farm**
   ```python
   crop_repo.get_active_by_farm(farm.id)
   ```

2. **Get active crop season by farmer**
   ```python
   crop_repo.get_active_by_farmer(farmer.id)
   ```

3. **Get today's activities for crop**
   ```python
   activity_repo.get_today_activities(crop.id, today)
   ```

4. **Get all farms by farmer**
   ```python
   farm_repo.get_all_by_farmer(farmer.id)
   ```

5. **Get all crop seasons for farm**
   ```python
   crop_repo.get_all_by_farm(farm.id)
   ```

6. **Get current stage for crop**
   ```python
   crop_stage_repo.get_active_by_crop_season(crop.id)
   ```

7. **Get next stage after current**
   ```python
   crop_stage_repo.get_next_stage(crop_season_id, current_stage_order)
   ```

8. **Get first pending stage**
   ```python
   crop_stage_repo.get_first_pending_stage(crop.id)
   ```

9. **Delete expired sessions**
   ```python
   session_repo.delete_expired_sessions(now)
   ```

10. **Get all farms (general)**
    ```python
    farm_repo.get_all()
    ```

## Migrations

The project uses **Alembic** for database migrations (configuration in `backend/`). All model changes should generate new migrations via:

```bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

Migration files are stored in `backend/alembic/` directory (not shown in glob results but configured).

---
*Database schema analyzed from codebase as of 2026-11-21. All models, fields, constraints, and indexes verified from `backend/app/database/models.py` and module-level model files.*