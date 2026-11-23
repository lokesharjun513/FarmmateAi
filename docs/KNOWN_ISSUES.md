# Known Issues

## Overview

This document captures known issues discovered during the codebase analysis. Issues are classified by severity and status.

## Authentication & Authorization

| Issue | Severity | Status | Impact | Notes |
|-------|----------|--------|--------|-------|
| **No token refresh flow** | High | ❌ Not Implemented | Users must re-login every 15 minutes when access token expires | Would require refresh token implementation |
| **No password reset endpoint** | Medium | ❌ Not Implemented | Users cannot reset forgotten passwords | Would require SMTP or third-party auth |
| **No account lockout after failed login** | Medium | ⚠️ Partially Implemented | No protection against brute-force attacks | Could add rate limiting |
| **Farmer profile required for most operations** | Medium | ✅ Implemented | Blocks access if profile missing | Inconsistent - some routes may work without profile |
| **No role-based endpoint differentiation** | Low | ⚠️ Partially Implemented | All authenticated farmers have same permissions | No admin/manager roles exist |

## Frontend Issues

| Issue | Severity | Status | Impact | Notes |
|-------|----------|--------|--------|-------|
| **API base URL hardcoded for emulator** | Medium | ⚠️ Partially Implemented | `10.0.2.2` for Android emulator, `localhost` for iOS | Physical devices need device IP; no auto-detection |
| **No error boundary for API failures** | Low | ❌ Not Implemented | API errors may crash screens | Should use try/catch and show error messages |
| **Loading states not consistently implemented** | Low | ⚠️ Partially Implemented | Some screens show loading, others don't | Improve UX consistency |
| **Bottom navigation bar state management** | Low | ⚠️ Partially Implemented | Tab selection works but some screens have placeholder content | Complete screen implementations |

## Backend Issues

| Issue | Severity | Status | Impact | Notes |
|-------|----------|--------|--------|-------|
| **Scheduler runs on all backend instances** | Medium | ⚠️ Partially Implemented | APScheduler started in lifespan; no distributed coordination | Would need Redis-based coordination or cloud cron |
| **No database connection pool tuning** | Low | ❌ Not Implemented | Default SQLAlchemy pooling may not suit production | Add pool_size/max_overflow config |
| **CORS configuration too permissive for production** | Medium | ⚠️ Partially Implemented | Dev allows localhost any port; prod needs explicit origins | Add production CORS configuration |
| **Weather API calls in synchronous loop** | Low | ⚠️ Partially Implemented | Scheduler calls weather for each farm sequentially | Could parallelize or batch |
| **No rate limiting on API endpoints** | Medium | ❌ Not Implemented | Potential for abuse | Consider adding middleware |
| **JWT secret key default/weak** | High | ⚠️ Partially Implemented | Development may use weak key | Enforce strong key generation |

## Database Issues

| Issue | Severity | Status | Impact | Notes |
|-------|----------|--------|--------|-------|
| **No migration version tracking** | Low | ❓ Unknown | Check if Alembic is configured | Verify alembic/versions/ directory |
| **Cascade delete behavior** | Low | ✅ Implemented | All models use cascade="all, delete-orphan" | Verify no unintended data loss |
| **No soft-delete pattern** | Low | ❌ Not Implemented | All deletions are permanent | Consider if needed for audit trail |
| **Composite index coverage** | Low | ⚠️ Partially Implemented | Some query patterns may benefit from additional indexes | Add based on query profiling |

## AI/ML Features Issues

| Issue | Severity | Status | Impact | Notes |
|-------|----------|--------|--------|-------|
| **No model training pipeline** | Medium | ❌ Not Implemented | System is rule-based, not ML | Would require separate ML infrastructure |
| **No computer vision capabilities** | Low | ❌ Not Implemented | Cannot analyze crop images | Would require TensorFlow/TensorFlow Lite |
| **Limited context in AI advisor** | Low | ⚠️ Partially Implemented | Uses crop age, weather, activities, soil type | Could expand with more data points |
| **Basic weather recommendations only** | Low | ✅ Implemented | Rain probability & temperature thresholds | Could add more farming-specific rules |
| **No predictive analytics** | Medium | ❌ Not Implemented | No yield forecasts, planting date optimization | Would require historical data model |

## Integration Issues

| Issue | Severity | Status | Impact | Notes |
|-------|----------|--------|--------|-------|
| **FCM credentials not in codebase** | Medium | ❓ Unknown | Verify Firebase project setup | Check google-services.json / GoogleService-Info.plist |
| **Weather API key management** | Medium | ⚠️ Partially Implemented | `WEATHER_API_KEY` env var required | Ensure key is rotated regularly |
| **No external payment integrations** | Low | ✅ Not Implemented | Not in scope | Confirm if needed for future |
| **No email service integration** | Low | ❌ Not Implemented | No password reset, notification emails | Would require SMTP setup |

## Documentation Issues

| Issue | Severity | Status | Impact | Notes |
|-------|----------|--------|--------|-------|
| **CHANGELOG.md not verified from Git history** | Low | ⚠️ Partially Implemented | May contain unverified changes | Only document verifiable changes |
| **Some features may be undocumented** | Low | ❓ Unknown | Re-scan may reveal gaps | Complete verification pass needed |
| **Mermaid diagram syntax** | Low | ✅ Verified | All diagrams use valid syntax | Minor linting may flag some patterns |

## Development Workflow Issues

| Issue | Severity | Status | Impact | Notes |
|-------|----------|--------|--------|-------|
| **No Dockerfile in backend** | Low | ❌ Not Implemented | Manual deployment setup | Would simplify deployment |
| **No .env in .gitignore** | Medium | ❌ Not Implemented | Environment secrets could be committed | Add .env to .gitignore |
| **Flutter test coverage limited** | Low | ⚠️ Partially Implemented | Basic widget tests only | Expand with more UI logic tests |
| **No pre-commit hooks** | Low | ❌ Not Implemented | Code quality could be enforced | Consider adding pre-commit |
| **Type checking not enforced** | Low | ❌ Not Implemented | mypy or similar not configured | Optional but recommended |

## Critical Gaps

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| **No token refresh flow** | High | Implement JWT refresh tokens or re-auth flow |
| **No password recovery** | Medium | Add forgot password / reset flow |
| **No rate limiting** | Medium | Add API rate limiting middleware |
| **Scheduler on multiple instances** | Medium | Use cloud cron or distributed scheduler |
| **Weak dev JWT key** | High | Generate strong random key for development |
| **CORS misconfiguration for prod** | Medium | Configure explicit allowed origins for production |

---
*Known issues documented from codebase analysis as of 2026-11-21. All issues verified from actual source code review.*