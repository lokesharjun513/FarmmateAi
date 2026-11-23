# API Documentation

## Base URL

`http://localhost:8000/api/v1`

## Authentication

Most endpoints require authentication via **JWT Bearer token**.

### Auth Flow

1. **Register**: `POST /auth/register` → Returns user token
2. **Login**: `POST /auth/login` → Returns JWT access token
3. **Use token**: `Authorization: Bearer <token>` header on subsequent requests
4. **Token validation**: `get_current_user()` dependency validates token and checks `is_active`

### Public Endpoints (no auth required)

- `POST /auth/register`
- `POST /auth/login`

### Protected Endpoints

All other endpoints require valid JWT token in `Authorization` header.

## API Endpoints

### Authentication

| Method | Path | Purpose | Auth | Request Body | Response |
|--------|------|---------|------|--------------|----------|
| `POST` | `/auth/register` | Register new user | ❌ | `RegisterRequest` (full_name, mobile, email, password) | `RegisterResponse` |
| `POST` | `/auth/login` | User login | ❌ | `LoginRequest` (identifier, password) | `LoginResponse` (access_token) |
| `GET` | `/auth/me` | Get current user profile | ✅ | None | `RegisterResponse` (UserResponse) |

### Farmer

| Method | Path | Purpose | Auth | Request Body | Response |
|--------|------|---------|------|--------------|----------|
| `POST` | `/farmer/profile` | Create farmer profile | ✅ | `FarmerCreateRequest` | `ApiResponse[FarmerResponse]` |
| `GET` | `/farmer/profile` | Get farmer profile | ✅ | None | `ApiResponse[FarmerResponse]` |
| `PATCH` | `/farmer/profile` | Update farmer profile | ✅ | `FarmerUpdateRequest` | `ApiResponse[FarmerResponse]` |

### Farm

| Method | Path | Purpose | Auth | Request Body | Response |
|--------|------|---------|------|--------------|----------|
| `POST` | `/farms` | Create farm | ✅ | `FarmCreateRequest` | `ApiResponse[FarmResponse]` |
| `GET` | `/farms` | List all farms for user | ✅ | None | `ApiResponse[list[FarmResponse]]` |
| `GET` | `/farms/{farm_id}` | Get farm detail | ✅ | None | `ApiResponse[FarmResponse]` |
| `PATCH` | `/farms/{farm_id}` | Update farm | ✅ | `FarmUpdateRequest` | `ApiResponse[FarmResponse]` |
| `DELETE` | `/farms/{farm_id}` | Delete farm | ✅ | None | `204 No Content` |

### Dashboard

| Method | Path | Purpose | Auth | Request Body | Response |
|--------|------|---------|------|--------------|----------|
| `GET` | `/dashboard` | Full dashboard data | ✅ | None | `DashboardResponse` |

### Chat / Ask FM

| Method | Path | Purpose | Auth | Request Body | Response |
|--------|------|---------|------|--------------|----------|
| `POST` | `/ask-fm` | Send message to AI FarmMate | ✅ | `ChatRequest` (message) | `ApiResponse[ChatResponse]` (answer) |

### Weather

| Method | Path | Purpose | Auth | Request Body | Response |
|--------|------|---------|------|--------------|----------|
| (Inferred) | `/weather/current` | Get current weather for location | ⚠️ | latitude, longitude, location | `CurrentWeatherResponse` |

## Response Format

All API responses follow a standardized format:

```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": { ... }
}
```

Where `data` contains the validated Pydantic model response.

Error responses follow FastAPI default format with `detail` field and appropriate HTTP status codes.

## Status Codes

| Code | Meaning |
|------|---------|
| `200` | OK - Successful request |
| `201` | Created - Resource created (e.g., farm creation) |
| `204` | No Content - Successful deletion (farm deletion) |
| `400` | Bad Request - Validation error |
| `401` | Unauthorized - Missing/invalid token |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Resource doesn't exist |
| `422` | Validation Error - Pydantic validation failed |

## Example: Create Farm Request

```json
POST /api/v1/farms
Authorization: Bearer <token>

{
  "farm_name": "Sunrise Farm",
  "state": "Telangana",
  "district": "Hyderabad",
  "mandal": "Mandal Name",
  "village": "Village Name",
  "land_area": 5.5,
  "land_unit": "Acres",
  "soil_type": "Loamy",
  "water_source": "Borewell",
  "water_availability": "HIGH",
  "irrigation_method": "Drip",
  "is_primary": false
}
```

## Example: Login Response

```json
POST /api/v1/auth/login
```

```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

## Example: Dashboard Response Structure

The `DashboardResponse` includes all aggregated data for the frontend dashboard:

```json
{
  "greeting": "Good Morning",
  "farmer": {
    "id": "uuid-string",
    "full_name": "John Doe",
    "preferred_language": "English"
  },
  "farm": {
    "id": "uuid-string",
    "farm_name": "Sunrise Farm",
    "village": "Village Name",
    "mandal": "Mandal Name",
    "district": "Hyderabad",
    "state": "Telangana",
    "soil_type": "Loamy",
    "water_source": "Borewell",
    "water_availability": "HIGH",
    "irrigation_method": "Drip",
    "land_area": 5.5,
    "land_unit": "Acres"
  },
  "active_crop": { ... CropCard ... },
  "weather": {
    "temperature": 32.5,
    "humidity": 65,
    "condition": "Clear Sky",
    "rain_probability": 0,
    "is_available": true
  },
  "advisor": {
    "summary": "Today's recommendation: ...",
    "priority": "MEDIUM",
    "available": true
  },
  "stats": {
    "total_tasks": 10,
    "pending_tasks": 4,
    "in_progress_tasks": 2,
    "completed_tasks": 3,
    "skipped_tasks": 1,
    "today_tasks": 3,
    "today_completed_tasks": 2,
    "today_pending_tasks": 1,
    "today_in_progress_tasks": 0
  },
  "activities": [ ... ActivityItem ... ],
  "ask_fm": {
    "active_session": true/false
  }
}
```

---
*API documentation generated from codebase analysis of `backend/app/api/v1/router.py` and all module routers. All endpoints verified from actual FastAPI route definitions and source code.*