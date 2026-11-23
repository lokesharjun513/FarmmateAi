# External Integrations

## Weather API Integration

### Purpose
Provides current weather conditions and forecasts for farm locations.

### Provider Pattern
The weather service uses an **abstract provider pattern** allowing multiple weather APIs to be swapped.

### Current Implementation
- **WeatherProvider** (`backend/app/modules/weather/provider.py`): Default implementation
- **LocationProvider** (`backend/app/modules/weather/location_provider.py`): Resolves location names from coordinates

### API Calls Made

#### Get Current Weather
```
GET/POST to weather provider
Parameters: latitude, longitude
Response: Current weather data including:
- temperature
- humidity
- weather_condition
- wind_speed
- precipitation
- weather_code (mapped to condition strings)
- rain_probability (daily max precipitation probability)
- sunrise, sunset times
```

#### Get Weather Recommendation
```
Uses get_current_weather() result
Applies rule-based logic:
- rain_probability >= 70% → "Avoid irrigation, plan activities accordingly"
- temperature >= 35°C → "Check crop moisture, avoid heavy work during peak heat"
- Otherwise → "Conditions suitable for normal farm activities"
```

### Weather Code Mapping
```python
# From weather/service.py:_get_weather_condition()
0: "Clear Sky"
1: "Mainly Clear"
2: "Partly Cloudy"
3: "Overcast"
45: "Fog"
48: "Depositing Rime Fog"
51: "Light Drizzle"
53: "Moderate Drizzle"
55: "Dense Drizzle"
56: "Light Freezing Drizzle"
57: "Dense Freezing Drizzle"
61: "Slight Rain"
63: "Moderate Rain"
65: "Heavy Rain"
66: "Light Freezing Rain"
67: "Heavy Freezing Rain"
71: "Slight Snow"
73: "Moderate Snow"
75: "Heavy Snow"
77: "Snow Grains"
80: "Slight Rain Showers"
81: "Moderate Rain Showers"
82: "Violent Rain Showers"
85: "Slight Snow Showers"
86: "Heavy Snow Showers"
95: "Thunderstorm"
96: "Thunderstorm with Slight Hail"
99: "Thunderstorm with Heavy Hail"
```

### Location Resolution
```
Function: get_location_name(latitude, longitude)
Returns: String like "Village Name, District Name"
Used by: WeatherService.get_current_weather() to provide human-readable location
```

## Firebase Cloud Messaging (FCM) Integration

### Purpose
Push notifications to mobile app farmers.

### Implementation

#### Device Token Registration
```
Endpoint/Method: Register device token per farmer
Data stored: farmer_id, fcm_token, platform (iOS/Android/Web), active status
Repository: notifications/repository_device.py
Model: DeviceToken (farmer_id, token, platform, active, created_at)
```

#### Push Notification sending
```
Service: notifications/service.py / notifications/fcm_service.py
Method: Send notification to specific farmer or all farmers
Payload: title, message, type, priority, data fields
Transport: Firebase Cloud Messaging
```

#### Notification Types (from `notifications/models.py:NotificationType`)

| Type | Trigger | Description |
|------|---------|-------------|
| `AI_ADVISOR` | Scheduler daily run | "Today's AI Advice: ..." |
| `WEATHER_UPDATE` | Weather service fetch | "Weather update: ..." |
| `ACTIVITY_REMINDER` | Scheduled activities | "Reminder: Fertilization today" |
| `SYSTEM` | System events | "Your farm data updated" |

#### Notification Priorities (from `notifications/models.py:NotificationPriority`)

| Priority | Value | Usage |
|----------|-------|---------|
| `LOW` | 0 | Non-urgent information |
| `MEDIUM` | 1 | Important but not critical (default) |
| `HIGH` | 2 | Immediate attention required |

### FCM Message Format
```json
{
  "token": "<FCM_registration_token>",
  "notification": {
    "title": "Today's AI Advice",
    "body": "Check soil moisture before irrigation",
    "color": depending on priority
  },
  "data": {
    "type": "AI_ADVISOR",
    "priority": "MEDIUM",
    "farm_id": "...",
    "action": "open_dashboard"
  }
}
```

## Authentication (JWT)

### Purpose
Secure API access between Flutter frontend and FastAPI backend.

### Implementation
- **Library**: `python-jose[jwt]` 
- **Algorithm**: HS256 (HMAC with SHA256)
- **Secret key**: From environment variables (`SECRET_KEY`)
- **Algorithm configuration**: From `app/core/auth.py`

### Token Lifecycle
1. **Issuance**: `POST /auth/login` → returns JWT
2. **Usage**: `Authorization: Bearer <token>` header
3. **Validation**: `get_current_user()` dependency on each protected request
4. **Expiry**: 15 minutes (configurable)
5. **Invalidation**: On logout or account deactivation

### JWT Payload Claims
```text
{
  "sub": "<user_uuid>",     // Subject (user ID)
  "iat": <issued_at>,       // Issued at timestamp
  "exp": <expiration>,      // Expiration timestamp
  "refresh": True           // Custom claim
}
```

## Database (PostgreSQL)

### Purpose
Persistent data storage for all application data.

### Connection
- **URL**: From environment variable `DATABASE_URL` or configured in `settings`
- **Driver**: `psycopg2-binary`
- **ORM**: SQLAlchemy 2.x
- **Pooling**: Default SQLAlchemy connection pooling

### Connection Management
- `get_db()` dependency in `app/database/session.py`
- Provides new `Session` per request
- Automatically closed after request response

## API Ecosystem Summary

| Integration | Direction | Technology | Status |
|-------------|-----------|-----------|--------|
| **Weather API** | External → Backend | HTTP REST, provider pattern | ✅ Implemented |
| **Firebase Cloud Messaging** | Backend → Mobile | FCM HTTP/v1 API | ✅ Implemented |
| **JWT Authentication** | Internal service | Python-jose, HS256 | ✅ Implemented |
| **PostgreSQL** | Internal persistence | SQLAlchemy ORM | ✅ Implemented |
| **OpenAI / LLM** | External (potential) | API calls | ❌ Not Implemented |
| **Google Maps / Geocoding** | External (potential) | API calls | ❌ Not Implemented (location resolved internally) |
| **SMTP / Email service** | External (potential) | For password reset, notifications | ❌ Not Implemented |
| **Stripe / Payment** | External (potential) | Not in current scope | ❌ Not Implemented |

## Integration Points Summary

### Backend Initiated Externally

1. **Weather Provider API** - Called during:
   - Dashboard data retrieval
   - Scheduler daily job
   - AI advisor context assembly
   - Weather recommendation generation

2. **FCM Push Notifications** - Sent during:
   - Scheduler daily job (6 AM)
   - New advisor advice generated
   - System events

3. **JWT Token Validation** - On every protected API request

### Frontend Initiated Externally (from mobile app)

1. **API calls** to backend (all protected endpoints)
2. **Location services** (geolocator plugin) - for device location
3. **Shared preferences** - local storage of tokens, settings

### No Current Integrations

- ❌ Payment gateways (Stripe, PayPal, etc.)
- ❌ Email services (SMTP)
- ❌ Mapping APIs (Google Maps, here Maps)
- ❌ Social media login (Google, Apple, Facebook)
- ❌ Analytics services (Google Analytics, Firebase Analytics - partially, but not for tracking)
- ❌ Crash reporting (Fabric, Sentry - not configured)
- ❌ App stores (Play Console, App Store Connect - deployment only)
---
*External integrations documented from codebase analysis as of 2026-11-21. All integrations verified from actual source code.*