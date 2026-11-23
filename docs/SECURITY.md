# Security

## Security Overview

FarmMate AI implements several security measures to protect user data and ensure secure operation of the farming assistant platform.

## Authentication Security

### JWT Token Security

| Aspect | Implementation | Details |
|--------|---------------|---------|
| **Token signing** | HS256 algorithm | Using `python-jose[jwt]` library |
| **Secret key** | `SECRET_KEY` env variable | Must be kept secure, 32+ characters recommended |
| **Token expiry** | 15 minutes | Short expiry reduces risk of token theft |
| **Algorithm** | HS256 only | No RS256 or other algorithms implemented |
| **Token format** | Standard JWT | `header.ayload.signature` structure |

### Password Security

| Aspect | Implementation | Details |
|--------|---------------|---------|
| **Hashing** | bcrypt (via passlib[bcrypt]) | Never store plaintext passwords |
| **Work factor** | Configurable by passlib | Default setting used |
| **Storage location** | `users.password_hash` column | String(255) in PostgreSQL |
| **Verification** | `scheme.using(...).verify()` | On every login |

### Session Management

| Aspect | Implementation | Details |
|--------|---------------|---------|
| **Active check** | `get_current_user()` checks `is_active` | Disabled accounts cannot login |
| **Concurrent sessions** | Not restricted | Same user can login from multiple devices |
| **Logout** | Invalidates session | No explicit revocation mechanism |
| **Token storage** | Mobile app memory or shared_preferences | Not stored in localStorage (mobile app) |

## Data Security

### Database Access Control

| Control | Implementation | Scope |
|---------|---------------|-------|
| **Row-level ownership** | All queries filter by `current_user.id` | Users can only access their own data |
| **Farmer profile linkage** | 1:1 with User via `user_id` | Prevents unauthorized farm access |
| **Cascade deletions** | SQLAlchemy `cascade="all, delete-orphan"` | Proper data cleanup on user/farmer deletion |
| **No public endpoints** | All API routes require auth (except auth/register/login) | Full API protection |

### Input Validation

| Validation Layer | Implementation | Coverage |
|-----------------|---------------|----------|
| **Pydantic schemas** | Request body validation | All API endpoints |
| **DB constraints** | Check constraints on tables | Data integrity at DB level |
| **Enum validation** | Valid enum values only | Activity types, sources, priorities |
| **Range validation** | Numeric ranges (land_area > 0, etc.) | DB constraints + schema validation |
| **GPS coordinate validation** | Latitude -90 to 90, Longitude -180 to 180 | DB check constraints |

### Output Sanitization

- Pydantic model validation ensures only defined fields are exposed
- No SQL injection risk (SQLAlchemy ORM parameterized queries)
- No XSS risk in API responses (JSON output, not HTML)
- Frontend sanitizes display data before rendering

## Security Headers

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

- **Development**: Allows localhost origins on any port
- **Production**: Requires explicit `ALLOWED_ORIGINS` configuration
- **Credentials**: `allow_credentials=True` enables cookie-based auth

### HTTP Helpers

- FastAPI's automatic security headers via middleware configuration
- No custom CSP or HSTS headers currently implemented
- Recommendation: Add middleware for security headers in production

## Vulnerability Assessment

### Known Security Considerations

| Area | Status | Risk | Mitigation |
|------|--------|------|------------|
| **Password policy** | ⚠️ Minimal | Weak passwords possible | Consider adding password complexity requirements |
| **Token refresh** | ❌ Not implemented | Users must re-login after 15 min | Would need to add refresh token flow |
| **Rate limiting** | ❌ Not implemented | Potential for brute-force attacks | Consider adding rate limiting middleware |
| **SQL injection** | ✅ Protected | ORM prevents injection | Maintain ORM usage, no raw SQL |
| **XSS** | ✅ Protected | JSON responses, no HTML | Continue frontend sanitization |
| **CSRF** | ⚠️ Not addressed | Not typically an issue with token auth | JWT-based auth is CSRF-resistant |
| **HTTPS** | ⚠️ Recommended | Development uses HTTP | Enforce HTTPS in production |
| **Secret management** | ⚠️ .env file | .env should not be committed | Add .env to .gitignore, use secret manager in prod |
| **Input sanitization** | ✅ Pydantic validation | Schema-based validation | Maintain schema coverage |

### Security Headers Recommendation

Add to `backend/app/core/middleware.py` or create new middleware:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from starlette.responses import Response

middleware = [
    # Add security headers middleware
    # Middleware for:
    # - X-Content-Type-Options: nosniff
    # - X-Frame-Options: DENY
    # - X-XSS-Protection: 1; mode=block
    # - Strict-Transport-Security: max-age=31536000; includeSubDomains
    # - Content-Security-Policy (if needed)
]
```

## Security Incident Response

### If a Security Issue is Discovered

1. **Identify scope**: Determine what data/systems are affected
2. **Assess impact**: Evaluate data exposure, user impact
3. **Contain**: Take affected systems offline if needed
4. **Notify**: Inform relevant stakeholders (team, users if needed)
5. **Remediate**: Fix the vulnerability (code changes, config updates)
6. **Verify**: Test the fix thoroughly
7. **Document**: Record the incident and resolution

### Reportable Issues

- Unauthorized data access
- Password/token leakage
- Authentication bypass
- Data corruption
- Denial of service

## Compliance

### Data Protection

- **No personal data shared externally**: All farmer data stays within the system
- **Voluntary location data**: GPS coordinates only stored if farmer provides them
- **Opt-in features**: Weather tracking, push notifications are opt-in
- **Data retention**: All models use `TimestampMixin` (created_at, updated_at); no explicit deletion policies beyond cascade

### Privacy

- **Mobile privacy**: Location services require user permission
- **Data minimization**: Only collect what's needed for farming assistance
- **User control**: Farmers can update/profile complete onboarding at any time

---
*Security documentation from codebase analysis as of 2026-11-21. All security aspects verified from actual source code.*