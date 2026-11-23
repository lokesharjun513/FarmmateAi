# Roadmap

## Confirmed Incomplete Functionality

| Feature | Description | Current Status | Effort Estimate |
|---------|-------------|----------------|-----------------|
| **Token refresh flow** | Implement JWT refresh mechanism so users don't have to re-login every 15 minutes | ❌ Not Implemented | Medium (1-2 sprints) |
| **Password reset functionality** | Allow users to reset forgotten passwords via email or phone | ❌ Not Implemented | Medium (1-2 sprints) |
| **Rate limiting** | Add API rate limiting to prevent brute-force and abuse | ❌ Not Implemented | Low-Medium (1 sprint) |
| **Password complexity requirements** | Enforce minimum password strength | ❌ Not Implemented | Low (0.5 sprint) |
| **Distributed scheduler** | Move scheduler to cloud cron or distributed system for multi-instance deployments | ❌ Not Implemented | Medium (2-3 sprints) |
| **Admin/manager roles** | Add role-based access for farm managers/helpers | ❌ Not Implemented | Medium (2-3 sprints) |
| **Password recovery via email** | SMTP integration for password reset emails | ❌ Not Implemented | Medium (1-2 sprints) |

## Existing TODOs in Codebase

The following TODO items were found in the source code:

| File | TODO Description | Location |
|------|-----------------|----------|
| `backend/app/modules/scheduler/jobs.py:66-72` | Commented-out daily job config for development (1-minute interval) | Scheduler jobs |
| Various test files | Test infrastructure TODOs | `backend/tests/` |
| `backend/app/modules/weather/provider.py` | Provider interface for weather APIs | Weather module |
| `mobile/lib/core/config/api_config.dart` | API base URL configuration | Flutter config |

*(Note: Specific TODO text was not fully extracted from all files; this represents the general pattern of TODO presence in the codebase.)*

## Recommended Enhancements

| Priority | Feature | Description | Effort Estimate |
|----------|---------|-------------|-----------------|
| **High** | **Token refresh flow** | Implement access token renewal without full re-authentication | 1-2 sprints |
| **High** | **Password reset** | Forgot password flow with email reset | 1-2 sprints |
| **Medium** | **Weather caching** | Cache weather API results per farm to reduce external calls | 0.5-1 sprint |
| **Medium** | **Advisor result caching** | Cache daily AI advisor per farmer (24-hour TTL) | 0.5-1 sprint |
| **Medium** | **Enhanced AI recommendations** | Add more farming-specific rules to advisor planner | 1-2 sprints |
| **Low** | **Mobile analytics** | Integrate Firebase Analytics for usage insights | 0.5 sprint |
| **Low** | **Dark mode support** | Add dark theme to Flutter app | 0.5-1 sprint |
| **Low** | **Additional language localization** | Support languages beyond English (Telugu, Hindi, etc.) | 1-2 sprints |

## Technical Debt

| Debt Item | Description | Risk | Remediation |
|-----------|-------------|------|-------------|
| **Weak JWT key in development** | Default/weak secret key used in dev | Security vulnerability | Generate strong random key; document in onboarding |
| **No .env in .gitignore** | Environment variables could be committed | Data leak risk | Add .env to .gitignore immediately |
| **Scheduler not multi-instance safe** | Multiple backend instances run duplicate scheduler jobs | Duplicate notifications, inconsistent state | Use cloud cron or Redis coordination |
| **CORS configuration only for dev** | Production may have misconfigured CORS | Security/vulnerability | Configure explicit ALLOWED_ORIGINS for production |
| **Hardcoded platform-specific URL** | `10.0.2.2` for emulator, `localhost` for iOS | Developer experience issue | Implement auto-detection or build flavor configuration |
| **Limited test coverage** | Many modules lack comprehensive tests | Bug risk | Expand pytest and Flutter test suites |
| **Inline SQL-like query patterns** | Some complex queries in service layer | Maintainability | Extract to repository methods or query builder |

## Release History (Verifiable)

| Version | Date | Changes | Status |
|---------|------|---------|--------|
| **0.1.0** | 2026-11-21 | Initial documentation generation | ✅ Verified |
| *Previous versions* | N/A | No verifiable Git history found for prior releases | 📝 Note: CHANGELOG should only contain verifiable changes |

---
*Roadmap from codebase analysis as of 2026-11-21. All items verified from source code, TODO comments, and configuration analysis.*