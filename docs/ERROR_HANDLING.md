# Error Handling

## Overview

The application uses a **centralized error handling** approach with FastAPI's exception handlers. All errors follow consistent patterns for status codes, response formats, and logging.

## Exception Handlers

### Core Exception Handlers (`backend/app/core/exception_handlers.py`)

The following exception handlers are registered in `main.py`:

| Exception | HTTP Status | Response Format | When Raised |
|-----------|-------------|-----------------|-------------|
| **HTTPException** (FastAPI) | As specified | `{"detail": "..."}` | Explicit raises in routes/services |
| **Validation Error** (Pydantic) | 422 | `{"detail": [...]} | Invalid request body/query |
| **404 Not Found** | 404 | `{"detail": "..."}` | Resource doesn't exist (e.g., farm not found) |
| **401 Unauthorized** | 401 | `{"detail": "..."}` | Missing/invalid JWT token |
| **403 Forbidden** | 403 | `{"detail": "..."}` | Insufficient permissions |
| **ValidationError** (custom) | 422 | `{"detail": "..."}` | Business rule violations |

### Custom Exception Classes (`backend/app/shared/exceptions.py`)

```python
class ValidationError(Exception):
    """Raised when input validation fails."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
```

Usage in services:
```python
from app.shared.exceptions import ValidationError

raise ValidationError("Farmer has no farms.")
```

## HTTP Error Responses

### Standard Error Format

All error responses follow FastAPI's default format:

```json
{
  "detail": "Error description here"
}
```

### Common Status Codes

| Status Code | Meaning | Example |
|-------------|---------|---------|
| `200` | OK | Successful GET request |
| `201` | Created | Successful POST (farm creation) |
| `204` | No Content | Successful DELETE (farm deletion) |
| `400` | Bad Request | Invalid input data, validation failure |
| `401` | Unauthorized | Missing or invalid JWT token |
| `403` | Forbidden | authenticated but not authorized |
| `404` | Not Found | Resource doesn't exist (e.g., `/farms/9999`) |
| `422` | Unprocessable Entity | Validation error, invalid data format |

### Example Error Responses

#### 404 Not Found - Farmer Profile

```http
GET /api/v1/farmer/profile
Authorization: Bearer <token>

# Response (farmer doesn't exist for this user):
{
  "detail": "Farmer profile not found."
}
```

#### 422 Validation Error - Invalid Farm Data

```http
POST /api/v1/farms
Authorization: Bearer <token>
Content-Type: application/json

# Request (missing required fields):
{
  "farm_name": "Test"
  # missing: land_area, state, etc.
}

# Response:
{
  "detail": [
    {
      "loc": ["body", "land_area"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "state"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 401 Unauthorized - Missing Token

```http
GET /api/v1/dashboard

# Response (no Authorization header):
{
  "detail": "Not authenticated"
}
```

## Error Handling Patterns

### Route-Level Error Handling

```python
@router.get("/{farm_id}", response_model=ApiResponse[FarmResponse])
def get_farm_endpoint(
    farm_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer_repository = FarmerRepository(db)
    farmer = farmer_repository.get_by_user_id(current_user.id)
    
    if farmer is None:
        raise FarmerProfileNotFoundError()  # raises 404
    
    farm_repository = FarmRepository(db)
    farm = get_farm(repository=farm_repository, farm_id=farm_id, farmer_id=farmer.id)
    
    if farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found."
        )
    
    return ApiResponse(
        success=True,
        message="Farm retrieved successfully.",
        data=FarmResponse.model_validate(farm),
    )
```

### Service-Level Error Handling

```python
# From advisor/service.py
async def get_today_advice(current_farmer: Farmer) -> DailyAdvisorResponse:
    farms = self.farm_repository.get_all_by_farmer(current_farmer.id)
    
    if not farms:
        raise ValidationError("Farmer has no farms.")
    
    farm = next(
        (farm for farm in farms if farm.is_primary),
        farms[0],
    )
    
    if farm.latitude is None or farm.longitude is None:
        raise ValidationError(
            "Farm location is required to generate daily advice."
        )
    
    # ... more validation
```

### Global Error Handler

FastAPI registers these handlers automatically. They convert exceptions to consistent HTTP responses.

```python
# From backend/app/main.py:52
register_exception_handlers(app)
```

## Logging

### Logger Configuration

```python
import logging

logger = logging.getLogger(__name__)
```

### Log Levels Used

| Level | When Used | Example |
|-------|-----------|---------|
| `DEBUG` | Detailed debugging information | `logger.debug("Query: %s", query)` |
| `INFO` | Normal operation confirmation | `logger.info("Scheduler started successfully")` |
| `WARNING` | Unexpected but not error | `logger.warning("Weather update failed for farm %s", farm.id)` |
| `ERROR` | Error occurred | `logger.error("Advisor generation failed: %s", error)` |
| `exception` | Error with stack trace | `logger.exception("Scheduler execution failed")` |

### Log Locations

- **Console**: uvicorn output when running in development
- **Files**: Potential log file configuration (not explicitly configured in current codebase)
- **Structured**: Includes timestamp, logger name, level, message

### Example Log Messages from Codebase

```python
# From scheduler/jobs.py:38-41
logger.info(
    "Scheduler completed successfully: %s",
    result.model_dump(),
)

# From scheduler/jobs.py:44-47
logger.exception(
    "Scheduler execution failed.",
)

# From scheduler/service.py:100-103
logger.exception(
    "Weather update failed for farm %s", farm.id,
)

# From scheduler/service.py:153-156
logger.info(
    "Advisor notification created for farmer %s",
    farmer.id,
)
```

## Validation Error Details

### Pydantic Validation

When request body fails Pydantic validation:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required"|"str is too short"|"str is too long"|etc.",
      "type": "error_type"
    }
  ]
}
```

### Custom Validation (ValidationError)

```json
{
  "detail": "Custom error message from service layer"
}
```

### Common Validation Errors

| Error Type | Cause | Resolution |
|------------|-------|------------|
| `field required` | Missing required field in request body | Add the field to request |
| `str is too short` | String too short for schema min_length | Provide longer value |
| `str is too long` | String exceeds max_length | Shorten the value |
| `invalid enum value` | Value not in allowed enum | Use valid enum value |
| `greater than 0` | Numeric value ≤ 0 (e.g., land_area) | Provide positive value |
| `ensure this value is greater than or equal to minimum` | Duration < 1 minute | Provide ≥ 1 value |

## Graceful Degradation

### Weather Service Failures

When weather API calls fail (network issues, invalid coordinates):

```python
# From dashboard/service.py:_get_weather()
try:
    weather = await self.weather_service.get_current_weather(...)
    return WeatherCard(..., is_available=True)
except Exception:
    return WeatherCard(
        temperature=0,
        humidity=0,
        condition="Unavailable",
        rain_probability=None,
        is_available=False,
    )
```

### Advisor Service Failures

```python
# From dashboard/service.py:_get_advisor()
try:
    advisor = await self.advisor_service.get_today_advice(current_farmer)
    return AdvisorCard(summary=advisor.summary, priority=advisor.priority, available=True)
except Exception:
    return AdvisorCard(
        summary="FarmMate AI recommendations are temporarily unavailable.",
        priority="LOW",
        available=False,
    )
```

## Error Handling Best Practices

### Do's

1. **Use specific exceptions** rather than bare `except`
2. **Log errors** with appropriate context (farm ID, user ID, etc.)
3. **Return consistent error formats** across all endpoints
4. **Validate input early** at route level before business logic
5. **Handle expected failures** gracefully (weather API downtime, etc.)
6. **Document error cases** in API documentation

### Don'ts

1. **Don't expose raw SQL errors** to clients
2. **Don't ignore exceptions** without logging
3. **Don't return generic 500 errors** for client errors (use 4xx codes)
4. **Don't validate late** (let Pydantic handle schema validation)
5. **Don't forget to check** `farmer is None` before farm operations
6. **Don't hardcode error messages**; use centralized exceptions

---
*Error handling documentation from codebase analysis as of 2026-11-21. All error patterns verified from actual source code in `backend/app/core/exception_handlers.py`, middleware, and module services.*