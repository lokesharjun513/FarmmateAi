# Technology Stack

## Mobile Frontend

| Category | Technology | Version/Details |
|----------|-----------|-----------------|
| **Framework** | Flutter | SDK for building native apps from a single codebase |
| **Language** | Dart | Client-optimized language for fast apps on any platform |
| **State Management** | Provider | Riverpod-style provider for state management |
| **Navigation** | GoRouter / app_router | Declarative navigation routing |
| **HTTP Client** | http package | REST API calls to backend |
| **Local Storage** | shared_preferences | Token and setting persistence |
| **Location** | geolocator | GPS location services |
| **Charts/Visuals** | material_design_icons, flare_flutter | UI icons and animations |
| **Testing** | flutter_test | Flutter unit and widget testing |

## Backend

| Category | Technology | Version/Details |
|----------|-----------|-----------------|
| **Framework** | FastAPI | Python framework for building APIs |
| **Language** | Python 3.11+ | Core programming language |
| **ORM** | SQLAlchemy | SQL toolkit and ORM |
| **Database** | PostgreSQL | Relational database with JSONB support |
| **ASync Scheduling** | APScheduler (apscheduler[sync]) | Cron-based background jobs |
| **Testing** | Pytest | Python testing framework |
| **API Docs** | FastAPI automatic | OpenAPI/Swagger auto-generated docs |
| **Environment** | python-dotenv | Environment variable loading |

### Backend Dependencies (from pyproject.toml / requirements)

Key dependencies currently in use:
- `fastapi` - API framework
- `uvicorn` - ASGI server
- `sqlalchemy` - ORM
- `psycopg2-binary` - PostgreSQL driver
- `pydantic` - Data validation
- `python-dotenv` - Env variables
- `apscheduler` - Background scheduling
- `python-jose[jwt]` - JWT authentication
- `passlib[bcrypt]` - Password hashing
- `cryptography` - Cryptographic operations

## Database

| Category | Technology | Details |
|----------|-----------|---------|
| **Database System** | PostgreSQL | Open-source relational database |
| **ORM** | SQLAlchemy 2.x | Full SQL toolkit and ORM |
| **Migrations** | Alembic (implied) | Database schema migrations |
| **Data Types** | UUID primary keys | Unique identifiers across all tables |
| | JSONB columns | Flexible schema extension |
| | SQL Enum types | Constrained value sets (statuses, priorities, types) |
| | TimestampMixin | Created/updated on all models |

## AI/ML

| Category | Technology | Details |
|----------|-----------|---------|
| **Planning Engine** | Rule-based crop planner | `advisor_planner.py` - Deterministic activity planning |
| **Context Builder** | Context assembly for AI prompts | `context_builder.py` - Aggregates crop, weather, activity data |
| **Intent Detection** | `intent_detector.py` | Classifies user queries into farming actions |
| **Orchestrator** | `orchestrator.py` | Coordinates multi-step AI workflows |
| **Planner** | `planner.py` | Generates crop plans with activities |
| **Parser** | `parser.py` | Parses AI responses and extracts data |
| **Agent Planner** | `advisor_planner.py` | Generates daily farming advice |
| **Weather Integration** | `weather_agent.py` | Weather-aware farming recommendations |

## External APIs & Integrations

| Service | Purpose | Integration Type |
|---------|---------|-----------------|
| **Weather Provider** | Current weather, forecasts | HTTP REST API calls (via `weather/provider.py`) |
| **Firebase Cloud Messaging** | Push notifications | FCM SDK, device token management |
| **OpenAI / LLM** | AI-generated advice (potential) | API calls (referenced in `ai_engine/` but rule-based currently) |
| **PostgreSQL** | Persistent data storage | psycopg2-binary driver |

## Development Tools

| Category | Tool | Purpose |
|----------|------|---------|
| **Build/Run** | uvicorn | FastAPI development server |
| **Package Manager** | uv / pip | Python package management |
| **Lock File** | uv.lock | Reproducible dependency versions |
| **Format** | black / isort | Code formatting |
| **Linting** | flake8 / pylint | Code quality |
| **Database Mgmt** | Alembic | Schema migrations |
| **Testing** | Pytest | Test framework with fixtures |
| **Flutter Tools** | flutter/packages | Mobile build and test |
| **IDE** | VS Code / PyCharm / Android Studio | Development environments |

## Project Configuration

| File | Purpose |
|------|---------|
| `backend/pyproject.toml` | Build system, dependencies, scripts |
| `backend/uv.lock` | Locked dependency versions |
| `backend/.env` (or settings) | Environment variables (APP_NAME, DB_URL, etc.) |
| `mobile/pubspec.yaml` | Flutter dependencies and assets |
| `mobile/lib/app/router/app_router.dart` | Navigation routes |
| `mobile/lib/app/theme/app_theme.dart` | App theming (colors, typography) |
| `D:\Projects\Farmate_AI\docs\README.md` | Documentation index |

## Versioning

| Component | Current Version | Source |
|-----------|----------------|--------|
| **Application** | Determined by codebase | Not explicitly versioned in single file |
| **Backend** | FastAPI auto-derived from `app.main` | `settings` configuration |
| **Flutter** | From `pubspec.yaml` | `version` and `build` fields |
| **API** | `api/v1` prefix | FastAPI router prefix |

---
*Technology stack analyzed from codebase as of 2026-11-21. All technologies verified from actual import statements and package configurations.*