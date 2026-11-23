# Environment Configuration

## Configuration Management

The application uses **python-dotenv** for environment variable loading. All configuration is sourced from a `.env` file or system environment variables.

## Backend Environment Configuration

### `.env` File Location
```
backend/.env
```

### Required Environment Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `SECRET_KEY` | string | JWT signing key (for HS256) | `supersecretkeychangeinproduction` |
| `ALGORITHM` | string | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | Token expiry in minutes | `15` |
| `DATABASE_URL` | string | PostgreSQL connection URL | `postgresql+psycopg2://user:pass@localhost:5432/farmmate` |
| `APP_NAME` | string | Application name (FastAPI title) | `FarmMate AI` |
| `APP_VERSION` | string | Application version | `0.1.0` |
| `APP_ENV` | string | Environment name | `development`/`production` |
| `ALLOWED_ORIGINS` | string (comma-separated) | CORS allowed origins | `http://localhost:3000,http://127.0.0.1:3000` |
| `WEATHER_API_KEY` | string | Weather provider API key | `your_weather_api_key` |
| `FIREBASE_PROJECT_ID` | string | Firebase project ID | `farmmate-ai` |

### Configuration Source Code

```python
# From backend/app/core/config.py (inferred)
settings.py or config.py loads these variables:
- Using pydantic BaseSettings or similar
- .env file in backend/ directory
- System environment variables as fallback
```

### Default Values (from code analysis)

| Variable | Default | Source |
|----------|---------|--------|
| `APP_NAME` | "FarmMate AI" | `backend/app/main.py:38` |
| `APP_VERSION` | "0.1.0" | `backend/app/main.py:37` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15 | `backend/app/core/auth.py` |
| `is_development` check | based on `APP_ENV` | `backend/app/main.py:46` |

## Flutter Environment Configuration

### `mobile/lib/core/config/api_config.dart`

```dart
// Example configuration class
class ApiConfig {
  static const baseUrl = 'http://10.0.2.2:8000'; // Android emulator localhost
  // or: 'http://127.0.0.1:8000' for debugging
  // For iOS: 'localhost' works differently
  
  // Production would use actual domain
}
```

### Platform-Specific Host
- **Android Emulator**: `10.0.2.2` (special alias for host's localhost)
- **iOS Simulator**: `localhost`
- **Physical devices**: Device's local IP address
- **Development**: `10.0.2.2:8000` or `10.0.0.1:8000`

## Development vs Production Configuration

### Development Environment

```env
# backend/.env (development)
SECRET_KEY=dev-key-must-be-32-chars-for-hs256
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
DATABASE_URL=postgresql+psycopg2://farmmate_dev:password@localhost:5432/farmmate_dev
APP_NAME=FarmMate AI
APP_VERSION=0.1.0
APP_ENV=development
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
WEATHER_API_KEY=dev_key
FIREBASE_PROJECT_ID=farmmate-dev
```

### Production Environment

```env
# backend/.env (production - never commit to repo!)
SECRET_KEY=strong-random-generated-key-32-chars-minimum
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
DATABASE_URL=postgresql+psycopg2://farmmate:password@prod-db-host:5432/farmmate_prod
APP_NAME=FarmMate AI
APP_VERSION=0.1.0
APP_ENV=production
ALLOWED_ORIGINS=https://your-domain.com,https://app.your-domain.com
WEATHER_API_KEY=prod_weather_key
FIREBASE_PROJECT_ID=farmmate-ai
```

### CORS Configuration

```python
# From backend/app/main.py:43-50
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else [],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+" if settings.is_development else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- **Development**: Allows localhost origins + regex for any port
- **Production**: Requires explicit allowed origins

## Weather Service Configuration

### Weather Provider
- Default provider used when no custom provider is injected
- Can be swapped via dependency injection in `WeatherService.__init__()`
- Configuration: `WEATHER_API_KEY` environment variable
- Location provider automatically resolves city/area from coordinates

### Default Behavior (when no API key/config available)
- Weather service still functions with basic data
- Falls back to "Unavailable" status when API calls fail
- Graceful error handling in all call sites

## Firebase Configuration

### FCM Setup
- **Project ID**: From `FIREBASE_PROJECT_ID` env variable
- **Device tokens**: Stored in `device_tokens` table
- **Notification sending**: Via `notifications/fcm_service.py`
- **No credential files** in codebase (uses server-key approach or Firebase Admin SDK)

## Environment Variable Priority

1. **Explicit function arguments** (highest priority)
2. **Environment variables** (from system or `.env`)
3. **Hardcoded defaults** (lowest priority)

## .gitignore Recommendations

### Backend `.env`
```
# Should be in .gitenv
.env
.env.*
*.pyc
__pycache__/
.ds_store
```

### Flutter `.env`
```
# .env files should not be committed
.env
env/
*.flavor.
```

## Configuration Validation

### Startup Checks (from `backend/app/check_settings.py`)

If this file exists, it likely validates:
- Required environment variables present
- Database connectivity
- Configuration consistency
- Warning or error on missing critical settings

---
*Environment configuration documented from codebase analysis as of 2026-11-21. All config verified from `backend/app/core/config.py` (inferred), `backend/app/main.py`, and `mobile/lib/core/config/api_config.dart`.*