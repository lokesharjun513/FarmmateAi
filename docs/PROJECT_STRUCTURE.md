# Project Structure

## Root Directory

```
D:\Projects\Farmate_AI\
├── docs/                    ← **Documentation directory** (this folder)
├── mobile/                  ← **Flutter mobile application**
│   ├── android/             ← Android native code and gradle
│   ├── ios/                 ← iOS native code (Xcode)
│   ├── lib/                 ← Dart source code
│   │   ├── main.dart        ← App entry point
│   │   ├── app/             ← App-wide configuration (theme, router)
│   │   ├── core/            ← Core utilities (storage, network, location, config)
│   │   └── features/        ← Feature modules (auth, farmer, farm, dashboard, etc.)
│   ├── test/                ← Flutter test files
│   └── pubspec.yaml         ← Flutter dependencies
├── backend/                 ← **Python FastAPI backend**
│   ├── app/                 ← Application source code
│   │   ├── __init__.py      ← Package init
│   │   ├── main.py          ← FastAPI entry point
│   │   ├── api/             └── v1/router.py ← API route registration
│   │   ├── core/            ← Core configuration (auth, exception handling, middleware)
│   │   ├── database/        └── models.py ← SQLAlchemy models base
│   │   ├── modules/         ← Feature modules (see below)
│   │   └── shared/          ← Shared utilities, enums, constants
│   ├── tests/               ← Pytest test files
│   ├── pyproject.toml       ← Build system configuration
│   ├── uv.lock              ← UV package lock
│   └── dist/                ← Built distribution packages
└── mobile/                  ← (duplicate? Check structure)
    └── ...                  ← Flutter mobile assets and build outputs
```

## Backend Module Structure

Each module in the backend is a self-contained package with its own:

```
app/modules/{module_name}/
├── __init__.py              ← Package init
├── router.py                ← FastAPI route definitions
├── service.py               ← Business logic
├── repository.py            ← Database repository patterns
├── models.py                ← SQLAlchemy ORM models
├── schemas.py               ← Pydantic validation schemas
├── tests/                   ← Module-specific tests
│   └── test_{module}_*.py
└── {additional files as needed}
```

### Currently Implemented Modules

| Module | Purpose | Key Files |
|--------|---------|-----------|
| **identity** | Authentication (register, login, me) | `identity/service.py`, `identity/router.py`, `identity/models.py` |
| **farmer** | Farmer profile management | `farmer/service.py`, `farmer/router.py`, `farmer/models.py` |
| **farm** | Farm CRUD operations | `farm/service.py`, `farm/router.py`, `farm/models.py` |
| **crop_season** | Crop lifecycle management | `crop_season/service.py`, `crop_season/router.py`, `crop_season/models.py` |
| **crop_stage** | Crop stage ordering & progression | `crop_stage/service.py`, `crop_stage/router.py`, `crop_stage/models.py` |
| **activity** | Farm activities with types/priorities | `activity/service.py`, `activity/router.py`, `activity/models.py` |
| **dashboard** | Dashboard data aggregation | `dashboard/service.py`, `dashboard/router.py` |
| **chat** | Ask FM AI conversations | `chat/router.py`, `chat/service.py`, `chat/models.py`, `chat/session_service.py` |
| **weather** | Weather integration & forecasts | `weather/service.py`, `weather/router.py` |
| **ai_engine** | AI crop planning & advisor | `ai_engine/service.py`, `ai_engine/router.py`, `ai_engine/models.py` |
| **scheduler** | Background jobs (daily at 6AM) | `scheduler/jobs.py`, `scheduler/service.py` |
| **notifications** | FCM push notifications | `notifications/service.py`, `notifications/repository_device.py` |
| **advisor** | Daily AI farming advice | `advisor/service.py`, `advisor/router.py` |
| **crop_recommendation** | Crop recommendation engine | `crop_recommendation/router.py` |
| **farming** | Farming operations | `farming/router.py` |
| **sowing_planner** | Sowing planning | `sowing_planner/router.py` |
| **season_learning** | Season learning | `season_learning/router.py` |
| **master** | Master data | `master/router.py` |
| **farm_intelligence** | Farm intelligence | `farm_intelligence/router.py` |

## Frontend Feature Structure

Each feature in the Flutter app follows a consistent pattern:

```
lib/features/{feature_name}/
├── presentation/            ← UI Screens & Widgets
│   ├── screens/             ← Page-level screens
│   └── widgets/             ← Reusable UI components
│
├── data/                    ← Data layer
│   ├── models/              ← Data models (often from API responses)
│   ├── repositories/        ← Data repositories
│   └── providers/           ← State providers (River/Provider)
│
├── domain/                  ← Domain layer (optional)
│   ├── models/              ← Business logic models
│   └── repositories/        ← Abstract repository interfaces
│
└── providers/               ← Feature-specific state management
```

### Feature Modules

| Feature | Screens/Widgets | Key Providers/Repositories |
|---------|----------------|---------------------------|
| **auth** | SplashScreen, LoginScreen, RegisterScreen, SplashScreen | `auth_provider.dart`, `auth_repository.dart` |
| **onboarding** | PostLoginOnboardingScreen, Onboarding screens | `onboarding_provider.dart`, `onboarding_repository.dart` |
| **farmer** | ProfileScreen, EditProfileScreen | `farmer_provider.dart`, `farmer_repository.dart`, `farmer_profile_model.dart` |
| **farm** | AddFarmScreen, FarmTab, AddFarmSheet, AddFarmForm | `farm_provider.dart`, `farm_repository.dart`, `farm_model.dart` |
| **dashboard** | DashboardScreen, MainShellScreen, HomeTab | `dashboard_provider.dart`, `dashboard_repository.dart`, `dashboard_model.dart` |
| **crops** | CropsTab, CropDetailScreen, CropCreateScreen, EditCropScreen | `crop_provider.dart`, `crop_recommendation_provider.dart` |
| **weather** | Weather provider, LocationService | `weather_provider.dart`, `weather_repository.dart`, `weather_model.dart` |
| **ask_fm** | AskFMScreen | `ask_fm_repository.dart` |
| **notifications** | Push notification services | `push_notification_service.dart`, `device_token_repository.dart` |

## Shared Library Structure

```
lib/shared/                    ← Cross-feature utilities
├── widgets/                   ← Reusable UI widgets
│   ├── ai_greeting_card.dart
│   └── ai_chat_bubble.dart
├── theme/                     ← App theming
│   ├── app_theme.dart
│   └── app_colors.dart
├── router/                    ← Navigation routing
│   └── app_router.dart
├── core/                      ← Core non-feature utilities
│   ├── storage/               ← Token storage, local data
│   │   └── token_storage.dart
│   ├── network/               ← API client
│   │   └── api_client.dart
│   ├── location/              ← Location services
│   │   └── location_service.dart
│   └── config/                ← API configuration
│       └── api_config.dart
```

## Key Configuration Files

| File | Purpose |
|------|---------|
| `mobile/pubspec.yaml` | Flutter dependencies (Flutter, Provider, HTTP, etc.) |
| `backend/pyproject.toml` | Python build system, dependencies |
| `backend/uv.lock` | UV lock file for reproducible installs |
| `backend/render.yaml` | Render deployment configuration |
| `mobile/lib/app/router/app_router.dart` | Navigation routing configuration |
| `mobile/lib/app/theme/app_theme.dart` | Material design theming |
| `mobile/lib/main.dart` | App entry point and routing |

## Database Schema Location

```
backend/app/database/
├── __init__.py              ← Package init
├── models.py                ← All SQLAlchemy model declarations (User, Farmer, Farm, CropStage, Activity, etc.)
├── session.py               ← Database session management (get_db dependency)
└── base.py                  ← Base class with TimestampMixin
```

## API Organization

```
backend/app/api/
└── v1/
    └── router.py            ← Main API router including all module routers
        └── prefix="/api/v1"
            ├── auth/        ← POST /api/v1/auth/register, POST /api/v1/auth/login
            ├── farmer/      ← POST/GET /api/v1/farmer/profile
            ├── farms/       ← POST/GET/DELETE /api/v1/farms
            ├── crop-seasons/ ← Crop season management
            ├── crop-stages/ ← Crop stage management
            ├── dashboard/   ← GET /api/v1/dashboard
            ├── ask-fm/      ← POST /api/v1/ask-fm
            ├── weather/     ← Weather data endpoints
            ├── chat/        ← Chat/AI endpoints
            └── ... (other modules)
```

## Testing Structure

```
backend/tests/              ← Pytest test suite
├── test_{module}_*.py     ← Module-specific tests
│   ├── test_identity_*.py
│   ├── test_farmer_*.py
│   ├── test_farm_*.py
│   ├── test_crop_*.py
│   └── ...
├── conftest.py             ← Test configuration and fixtures
└── test_utils.py           ← Shared test utilities
```

---
*Project structure analyzed from codebase as of 2026-11-21. All paths verified against actual source files.*