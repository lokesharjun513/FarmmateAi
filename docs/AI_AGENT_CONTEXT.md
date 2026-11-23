# AI Agent Context - FarmMate AI

## Project Purpose

FarmMate AI is an **AI-powered personal farming assistant** that helps farmers manage their crops, farms, and farming activities. The system combines traditional farm management features with AI-generated advice, weather integration, and automated scheduling.

The backend is a FastAPI application Python 3.11+ with PostgreSQL, and the frontend is a Flutter mobile app in Dart.

## Architecture Summary

### High-Level Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │  Flutter Mobile App │  │  FastAPI Backend    │ │
│  │  (Dart/Flutter)     │  │  (Python/FastAPI)   │ │
│  └─────────────────────┘  └─────────────────────┘ │
│           │                  │                      │
│           └───── HTTP/API ─────┘                      │
│                       └──────────────────────────────┘
│                    LAYERED ARCHITECTURE                    │
│  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │  Routes/Widgets     │  │  Services/Use Cases │ │
│  │  (API/UI)           │  │  (Business Logic)   │ │
│  └─────────────────────┘  └─────────────────────┘ │
│           │                  │                      │
│           └───── Dependencies ──────────────────────┘ │
│                 │                                              │
│        ┌─────────────────┐  ┌─────────────────────┐              │
│        │  Shared         │  │  External Services  │              │
│        │  Utilities      │  │  (Weather APIs, FCM)│              │
│        └─────────────────┘  └─────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### Module Structure (Backend)

The backend is organized into **independent modules**, each with its own router, service, repository, models, schemas, and tests:

| Module | Purpose | Key Files |
|--------|---------|-----------|
| **identity** | Authentication (register, login, me) | `identity/service.py`, `identity/router.py`, `identity/models.py` |
| **farmer** | Farmer profile management | `farmer/service.py`, `farmer/router.py`, `farmer/models.py` |
| **farm** | Farm CRUD operations | `farm/service.py`, `farm/router.py`, `farm/models.py` |
| **crop_season** | Crop lifecycle management | `crop_season/service.py`, `crop_season/router.py`, `crop_season/models.py` |
| **crop_stage** | Crop stage ordering & progression | `crop_stage/service.py`, `crop_stage/router.py`, `crop_stage/models.py` |
| **activity** | Farm activities with types/priorities | `activity/service.py`, `activity/router.py`, `activity/models.py` |
| **dashboard** | Dashboard data aggregation | `dashboard/service.py`, `dashboard/router.py` |
| **chat** | Ask FM AI conversations | `chat/router.py`, `chat/service.py`, `chat/models.py` |
| **weather** | Weather integration & forecasts | `weather/service.py`, `weather/router.py` |
| **ai_engine** | AI crop planning & advisor | `ai_engine/service.py`, `ai_engine/models.py` |
| **scheduler** | Background jobs (daily at 6 AM) | `scheduler/jobs.py`, `scheduler/service.py` |
| **notifications** | FCM push notifications | `notifications/service.py`, `notifications/repository_device.py` |
| **advisor** | Daily AI farming advice | `advisor/service.py`, `advisor/router.py` |
| +8 more modules | (farming, sowing_planner, season_learning, master, farm_intelligence, crop_recommendation, workflow) | |

### Key Data Models

**Core Models (SQLAlchemy, PostgreSQL)**:

| Model | Tables | Key Fields |
|-------|--------|-----------|
| **User** | `users` | `id (UUID PK)`, `full_name`, `mobile (UNIQUE)`, `email (UNIQUE)`, `password_hash`, `is_active` |
| **Farmer** | `farmers` | `id (UUID PK)`, `user_id (FK → users)`, `preferred_language`, `experience_years`, `profile_completion (0-100)`, `onboarding_completed` |
| **Farm** | `farms` | `id (UUID PK)`, `farmer_id (FK → farmers)`, `farm_name`, `state`, `district`, `mandal`, `village`, `latitude`, `longitude`, `land_area`, `land_unit`, `soil_type`, `water_source`, `water_availability`, `irrigation_method`, `is_primary` |
| **CropSeason** | `crop_seasons` | `id (UUID PK)`, `farm_id (FK → farms)`, `crop_name`, `crop_variety`, `land_area`, `land_unit`, `season (KHARIF/RABI/ZAID)`, `year`, `sowing_date`, `expected_harvest_date`, `harvested_date`, `status (PLANNED/ACTIVE/HARVESTED/CANCELLED)`, `is_active` |
| **CropStage** | `crop_stages` | `id (UUID PK)`, `crop_season_id (FK → crop_seasons)`, `name`, `description`, `stage_order`, `start_day`, `end_day`, `status (PENDING/ACTIVE/COMPLETED/SKIPPED)` |
| **Activity** | `activities` | `id (UUID PK)`, `crop_season_id (FK → crop_seasons)`, `stage_id (FK → crop_stages, SET NULL)`, `activity_type (18 types)`, `title`, `description`, `scheduled_date`, `original_scheduled_date`, `completed_date`, `status (PENDING/IN_PROGRESS/COMPLETED/SKIPPED)`, `priority (LOW/MEDIUM/HIGH/CRITICAL)`, `source (AI_PLANNED/WEATHER_TRIGGERED/FARMER_ADDED/SYSTEM)` |
| **AskFMSession** | `ask_fm_sessions` | `id (UUID PK)`, `farmer_id (FK → farmers)` |
| **AskFMMessage** | `ask_fm_messages` | `id (UUID PK)`, `session_id (FK → ask_fm_sessions)`, `message`, `ai_response` |
| **Notification** | `notifications` | `id (UUID PK)`, `farmer_id (FK → farmers)`, `type (AI_ADVISOR/WEATHER_UPDATE/ACTIVITY_REMINDER/SYSTEM)`, `priority (LOW/MEDIUM/HIGH)`, `is_read`, `title`, `message` |
| **DeviceToken** | `device_tokens` | `id (UUID PK)`, `farmer_id (FK → farmers)`, `token (FCM)`, `platform`, `active` |

### API Patterns

#### Base URL
```
http://localhost:8000/api/v1
```

#### Authentication
- `POST /auth/register` - Public, register new user
- `POST /auth/login` - Public, authenticate and get JWT token
- `GET /auth/me` - Protected, get current user profile (requires `Authorization: Bearer <token>`)

#### Protected Endpoints (all require valid JWT)
- `GET /farmer/profile` - Get farmer profile
- `POST /farmer/profile` / `PATCH /farmer/profile` - Create/update farmer profile
- `POST /farms` / `GET /farms` / `GET /farms/{id}` / `PATCH /farms/{id}` / `DELETE /farms/{id}` - Farm management
- `GET /dashboard` - Full dashboard data
- `POST /ask-fm` - Send message to AI FarmMate

#### Error Format
All errors follow FastAPI format:
```json
{"detail": "Error description here"}
```

Status codes: 200 (OK), 201 (Created), 204 (No Content), 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 422 (Validation Error).

### Database Conventions

- **All models inherit from `TimestampMixin`**: adds `created_at` and `updated_at`
- **Primary keys**: UUID (generated via `uuid.uuid4()`) across all tables
- **Foreign keys**: `ondelete="CASCADE"` or `ondelete="SET NULL"` as appropriate
- **Indexes**: Extensive use of composite indexes for query performance
- **SQL Enums**: All status/type fields use `SqlEnum` with named constraints
- **Check constraints**: Validation at DB level (e.g., land_area > 0, profile_completion 0-100)

### State Management (Frontend)

The Flutter app uses **Provider** for state management:

| Provider | Manages |
|----------|---------|
| `auth_provider.dart` | User auth state, token, login/logout |
| `farmer_provider.dart` | Farmer profile state |
| `farm_provider.dart` | Farm state and operations |
| `dashboard_provider.dart` | Dashboard data state |
| `crop_provider.dart` | Crop data state |
| `weather_provider.dart` | Weather data state |

### AI/ML Features

The system uses **rule-based AI** (not model training):

- **CropPlanner**: Generates activity plans based on crop parameters
- **AdvisorPlanner**: Generates daily farming advice from context
- **AIContext**: Aggregates crop, weather, activity, and soil data into prompt context
- **IntentDetector**: Classifies user queries into farming intents
- **Orchestrator**: Coordinates multi-step AI workflows
- **Parser**: Parses and formats AI responses

**Current AI capabilities**:
- Crop plan generation with scheduled activities
- Daily AI advisor with weather integration
- AI Q&A (Ask FM) with context-aware responses
- Weather-based recommendations (rain probability, temperature thresholds)

**Not implemented**: Model training, computer vision, predictive analytics, image-based disease detection

### External Integrations

| Service | Purpose | Integration Type |
|---------|---------|-----------------|
| **Weather Provider API** | Current weather, forecasts | HTTP REST API calls (provider pattern) |
| **Firebase Cloud Messaging** | Push notifications to mobile apps | FCM, device token management |
| **JWT Authentication** | Secure API access | HS256 signed tokens, 15-min expiry |
| **PostgreSQL** | Persistent data storage | SQLAlchemy ORM |

### Development Commands

#### Backend
```bash
cd D:\Projects\Farmate_AI\backend
uv sync                          # Install dependencies
uv run uvicorn app.main:app --reload  # Start dev server (port 8000)
alembic upgrade head             # Apply DB migrations
pytest                           # Run test suite
```

#### Frontend
```bash
cd D:\Projects\Farmate_AI\mobile
flutter pub get                  # Install Flutter packages
flutter doctor                   # Check environment
flutter run                      # Run on emulator/device
flutter test                     # Run widget/unit tests
flutter build apk --release      # Build release APK
```

#### Environment
```bash
# Required .env variables (backend/.env)
SECRET_KEY=your-32-plus-char-key
DATABASE_URL=postgresql://user:pass@host:port/db
APP_ENV=development|production
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
WEATHER_API_KEY=your-weather-key
FIREBASE_PROJECT_ID=farmmate-ai
ACCESS_TOKEN_EXPIRE_MINUTES=15
```

### Files to Not Modify Casually

**Critical files that should not be modified without careful consideration:**

1. `backend/app/database/models.py` - Core SQLAlchemy models; changing affects all module schemas
2. `backend/app/main.py` - FastAPI app entry point; lifespan, middleware, router registration
3. `backend/app/api/v1/router.py` - API route inclusion order and module registration
4. `backend/app/core/auth.py` - JWT authentication configuration (token expiry, algorithm)
5. `backend/app/core/config.py` - Environment variable configuration
6. `backend/app/shared/exceptions.py` - Custom exception definitions
7. `mobile/lib/main.dart` - Flutter app entry point, router, theme
8. `mobile/lib/app/router/app_router.dart` - Navigation route definitions
9. `mobile/lib/core/config/api_config.dart` - API base URL (affects all network calls)
10. `mobile/lib/core/storage/token_storage.dart` - Token persistence strategy

**Important**: When modifying any of these, verify ripple effects across:
- API endpoints (request/response schemas)
- Database migrations (model changes)
- Frontend screens (API call URLs, data flow)
- Authentication (token validation, user lookup)
- Scheduler functionality (if affected)

### Common Development Patterns

#### Adding a New API Endpoint

1. Define Pydantic schema in module's `schemas.py`
2. Implement service function in module's `service.py`
3. Add repository method in module's `repository.py` (if DB operation)
4. Create route in module's `router.py`
5. Register router in `backend/app/api/v1/router.py` (if new module)
6. Add frontend screen/widget (if UI needed)
7. Add test in `backend/tests/` and `mobile/test/`
8. Update documentation in `docs/` folder

#### Adding a New Database Model

1. Add model class in `backend/app/modules/{module}/models.py` (or `backend/app/database/models.py`)
2. Add SQLAlchemy columns with proper types, constraints, indexes
3. Create Alembic migration: `alembic revision --autogenerate -m "description"`
4. Apply migration: `alembic upgrade head`
5. Add repository methods in `repository.py` if needed
6. Add Pydantic schemas in `schemas.py` if API exposure needed
7. Update service logic in `service.py`
8. Update documentation

### Security Requirements

- **JWT tokens** must be sent via `Authorization: Bearer <token>` header
- **All protected endpoints** validate `get_current_user()` which checks `user.is_active`
- **Farmer profile** must exist for most operations (checked via `FarmerRepository.get_by_user_id(current_user.id)`)
- **No endpoint** should accept/return sensitive data without proper validation
- **Environment variables** containing secrets must not be committed (`.env` in `.gitignore`)

### Known Issues for AI Agents

| Issue | Impact | Workaround |
|-------|--------|-----------|
| **No token refresh flow** | Users re-login every 15 min | Plan re-auth moments in workflow |
| **No password reset** | Users can't reset forgotten passwords | Not applicable (out of scope for now) |
| **Scheduler on multi-instance** | Duplicate jobs if multiple backend instances | Only one instance should run scheduler, or use cloud cron |
| **CORS misconfiguration** | Production may reject requests | Ensure `ALLOWED_ORIGINS` includes production domain |
| **Weather API failures** | Graceful degradation available | Handle `is_available=False` in UI |
| **Farmer profile required** | Some ops block if profile missing | Check profile existence before operations |

### Quick Reference: Most Important Files

| Purpose | File Path |
|---------|-----------|
| Backend entry point | `backend/app/main.py` |
| API router | `backend/app/api/v1/router.py` |
| Authentication | `backend/app/modules/identity/` |
| Farmer model | `backend/app/modules/farmer/models.py` |
| Farm model | `backend/app/modules/farm/models.py` |
| Crop season model | `backend/app/modules/crop_season/models.py` |
| Activity model | `backend/app/modules/activity/models.py` |
| Dashboard service | `backend/app/modules/dashboard/service.py` |
| Chat/AI service | `backend/app/modules/chat/service.py` |
| Weather service | `backend/app/modules/weather/service.py` |
| Scheduler service | `backend/app/modules/scheduler/service.py` |
| Flutter main | `mobile/lib/main.dart` |
| Flutter router | `mobile/lib/app/router/app_router.dart` |
| Flutter API config | `mobile/lib/core/config/api_config.dart` |
| Auth provider | `mobile/lib/features/auth/providers/auth_provider.dart` |
| Farmer provider | `mobile/lib/features/farmer/providers/farmer_provider.dart` |

---
*This AI Agent Context document is designed to help future AI coding agents understand the project quickly and avoid breaking existing functionality. All information is grounded in source-code verification. Last updated: 2026-11-21.*

---
## Navigation

- **Documentation Index**: `docs/README.md`
- **Feature Overview**: `docs/PROJECT_OVERVIEW.md`
- **Architecture Diagrams**: `docs/ARCHITECTURE.md`
- **API Documentation**: `docs/API_DOCUMENTATION.md`
- **Database Schema**: `docs/DATABASE.md`
- **Feature Inventory**: `docs/FEATURE_MATRIX.md`
- **AI Agent Guidelines**: This file (`AI_AGENT_CONTEXT.md`)
- **Development Guide**: `docs/DEVELOPMENT_GUIDE.md`
- **Roadmap**: `docs/ROADMAP.md`
- **Known Issues**: `docs/KNOWN_ISSUES.md`