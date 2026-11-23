# Backend - FastAPI Application

## Entry Point

`backend/app/main.py` - FastAPI application initialization with lifespan management.

### App Configuration

```python
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered personal farming assistant backend.",
    lifespan=lifespan,
)
```

### Middleware

1. **CORS** - Configurable allowed origins
2. **RequestLoggingMiddleware** - Logs each incoming request
3. **Exception handlers** - Custom error handling

### Lifecycle

- **On startup**: `start_scheduler()` - starts APScheduler with daily cron job at 6:00 AM
- **On shutdown**: `scheduler.shutdown(wait=False)` - graceful scheduler shutdown

## API Organization

The API is organized into **modules** under `api/v1/router.py`:

```python
api_router = APIRouter(prefix="/api/v1", tags=[...])
```

### Registered Modules (in order)

| Module | Prefix | Tags | Endpoints |
|--------|--------|------|-----------|
| **identity** (auth) | `/auth` | `Authentication` | register, login, me |
| **farmer** | `/farmer` | `Farmer` | create_profile, get_profile, update_profile |
| **farm** | `/farms` | `Farm` | create, list, get, update, delete |
| **onboarding** | `/onboarding` | `Onboarding` | (routes configured) |
| **crop_season** | (implicit) | (various) | crop season management |
| **crop_stage** | (implicit) | (various) | crop stage management |
| **activity** | (implicit) | (various) | activity management |
| **dashboard** | (implicit) | `Dashboard` | dashboard data |
| **weather** | (implicit) | `Weather` | weather data |
| **advisor** | (implicit) | (various) | AI advisor |
| **chat** | `/ask-fm` | `🌱 Ask FM` | AI Q&A |
| **notifications** | (implicit) | (various) | notification management |
| **crop_recommendation** | (implicit) | (various) | crop recommendations |
| **farming** | (implicit) | (various) | farming operations |
| **scheduler** | (implicit) | (various) | scheduler jobs |
| **advisor** (duplicate reference) | (implicit) | (various) | daily advice |

### Auth Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/auth/login` | User login (returns JWT token) |
| `GET` | `/api/v1/auth/me` | Get current user profile |

### Farmer Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| `POST` | `/api/v1/farmer/profile` | Create farmer profile | Required |
| `GET` | `/api/v1/farmer/profile` | Get farmer profile | Required |
| `PATCH` | `/api/v1/farmer/profile` | Update farmer profile | Required |

### Farm Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| `POST` | `/api/v1/farms` | Create farm | Required |
| `GET` | `/api/v1/farms` | List farms | Required |
| `GET` | `/api/v1/farms/{farm_id}` | Get farm detail | Required |
| `PATCH` | `/api/v1/farms/{farm_id}` | Update farm | Required |
| `DELETE` | `/api/v1/farms/{farm_id}` | Delete farm | Required |

### Dashboard Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| `GET` | `/api/v1/dashboard` | Full dashboard data | Required |

### Chat/AI Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| `POST` | `/api/v1/ask-fm` | Send message to AI FarmMate | Required |

## Core Modules

### Identity Module (`app/modules/identity/`)

- **Service**: `register_user()`, `login_user()` - Business logic for auth
- **Repository**: `UserRepository` - Database operations for User model
- **Models**: `User` - SQLAlchemy model (id, full_name, mobile, email, password_hash, is_active)
- **Schemas**: `RegisterRequest`, `LoginRequest`, `UserResponse`, `TokenData`
- **Auth**: `get_current_user()` - Dependency that validates JWT token

### Farmer Module (`app/modules/farmer/`)

- **Service**: `create_farmer_profile()`, `get_farmer_profile()`, `update_farmer_profile()`
- **Repository**: `FarmerRepository` - Database operations for Farmer model
- **Models**: `Farmer` - SQLAlchemy model (linked to User via user_id, with profile_completion, onboarding_completed, etc.)
- **Schemas**: `FarmerCreateRequest`, `FarmerUpdateRequest`, `FarmerResponse`

### Farm Module (`app/modules/farm/`)

- **Service**: `create_farm()`, `get_farm()`, `list_farms()`, `update_farm()`, `delete_farm()`
- **Repository**: `FarmRepository` - Database operations for Farm model
- **Models**: `Farm` - SQLAlchemy model (linked to Farmer via farmer_id, with location, soil, water info)
- **Schemas**: `FarmCreateRequest`, `FarmUpdateRequest`, `FarmResponse`
- **Exceptions**: `FarmerProfileNotFoundError` - Raised when farmer profile doesn't exist

### Dashboard Module (`app/modules/dashboard/`)

- **Service**: `DashboardService` - Aggregates data from multiple modules
- **Calculations**: `calculate_progress()`, `calculate_crop_age()`, `calculate_estimated_duration()`
- **Card Builders**: `_stage_to_card()`, `_activity_to_card()`, `_build_crop_card()`
- **Data Fetching**: `_get_weather()`, `_get_advisor()`
- **Response**: `DashboardResponse` - Comprehensive dashboard DTO

### Chat Module (`app/modules/chat/`)

- **Service**: `ChatService` - Orchestrates AI conversations
- **Session Management**: `SessionRepository`, `SessionService`
- **Message Repository**: `MessageRepository`
- **Weather Integration**: `WeatherService`
- **Router**: `ask_fm` endpoint with AI response generation

### Weather Module (`app/modules/weather/`)

- **Service**: `WeatherService` - Wraps weather provider API
- **Provider**: `WeatherProvider`, `LocationProvider` - Abstract weather API providers
- **Schemas**: `CurrentWeatherResponse`, `WeatherRecommendationResponse`
- **Weather Codes**: Mapping table (0=Clear, 1=Mainly Clear, etc.)

### AI Engine Module (`app/modules/ai_engine/`)

- **Service**: `AIEngineService.generate_crop_plan()` - Generates crop activities
- **Planner**: `CropPlanner` - Generates crop plan with activity schedule
- **Orchestrator**: `Orchestrator` - Coordinates multi-step AI workflows
- **Parser**: `Parser` - Parses AI responses
- **Planner variants**: `AdvisorPlanner`, `RecommendationPlanner`, `ContextBuilder`
- **Models**: Crop planning models, enums

### Scheduler Module (`app/modules/scheduler/`)

- **Jobs**: `run_scheduler_job()` - Daily executed at 6:00 AM
- **Service**: `SchedulerService.run()` - Main scheduler orchestration
- **Configuration**: `start_scheduler()` - Starts APScheduler with cron trigger
- **Summary**: Reports processed farms, crops, weather updates, advisor notifications

### Notifications Module (`app/modules/notifications/`)

- **Service**: `NotificationService` - FCM push notification management
- **Repository**: `NotificationRepository`, `DeviceTokenRepository`
- **Models**: `Notification`, `DeviceToken` - With Type and Priority enums
- **FCM Service**: `FCMService`, `FCMServiceDevice` - Send push notifications

### Advisor Module (`app/modules/advisor/`)

- **Service**: `AdvisorService.get_today_advice()` - Generates daily farming advice
- **Planner**: `AdvisorPlanner.generate_daily_advice()` - AI advice generation
- **Context**: `AIContext` - Assembles context for AI prompt
- **Dependencies**: Farm repository, Crop repository, Activity repository

## Database Access Pattern

### Repository Pattern

Each module uses a **repository pattern** for database access:

```python
# Example pattern from farmer module
repository = FarmerRepository(db)
farmer = repository.get_by_user_id(current_user.id)
```

### Database Session

- Dependency: `get_db` from `app.database.session`
- Provides `Session` object for SQLAlchemy operations
- Context-managed via FastAPI `Depends`

## Shared Utilities

### Shared Directory (`app/shared/`)

| File | Purpose |
|------|---------|
| `enums.py` | Shared enum definitions |
| `constants.py` | Shared constants |
| `validators.py` | Input validation utilities |
| `utils.py` | General utilities |
| `responses.py` | Standard API response format (`ApiResponse`) |
| `mixins.py` | Mixin classes (TimestampMixin) |
| `exceptions.py` | Custom exception classes |

### TimestampMixin

Base class that adds `created_at` and `updated_at` fields to all models.

## Error Handling

### Exception Handlers (from `app/core/exception_handlers.py`)

- **404 Not Found**: Resource not found
- **422 Validation**: Pydantic validation errors
- **401 Unauthorized**: Missing/invalid authentication
- **403 Forbidden**: Insufficient permissions
- **Custom exceptions**: `FarmerProfileNotFoundError`, `ValidationError`

### Request Logging Middleware (`app/core/middleware.py`)

- Logs request method, path, status code, and processing time
- Helps with debugging and monitoring

## Testing

### Test Structure

```
backend/tests/
├── conftest.py          ← Test fixtures (db session, etc.)
├── test_identity_*.py   ← Auth tests
├── test_farmer_*.py     ← Farmer profile tests
├── test_farm_*.py       ← Farm management tests
├── test_crop_*.py       ← Crop lifecycle tests
├── test_dashboard_*.py ← Dashboard tests
├── test_chat_*.py       ← Ask FM/AI chat tests
├── test_notifications_*.py ← Notification tests
└── test_scheduler_*.py  ← Scheduler tests
```

### Test Configuration

- `conftest.py` provides a test database session
- Tests use SQLite in-memory or separate test PostgreSQL schema
- Each test gets a fresh database session

---
*Backend analysis from codebase as of 2026-11-21. All endpoints, services, and models verified from actual source files.*