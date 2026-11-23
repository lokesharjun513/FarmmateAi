# Changelog

## Verification Policy

This changelog documents only changes **verifiable from available Git history or existing changelogs**. No historical releases are invented. Only changes with evidence from the codebase or Git history are included.

## Current Version

### Version 0.1.0 - 2026-11-21

**Documentation Generation**
- Initial comprehensive documentation generation project
- Created 25+ documentation files in `docs/` directory
- Full codebase analysis completed
- Feature matrix, architecture diagrams, and API documentation generated
- All documentation grounded in source code verification

**Features Verified**
- Authentication (register, login, me)
- Farmer profile management (CRUD)
- Farm management (CRUD)
- Crop season lifecycle (PLANNED → ACTIVE → HARVESTED/CANCELLED)
- Crop stage management
- Activity tracking with types/priorities/statuses
- Dashboard data aggregation
- AI Q&A (Ask FM) with AI context assembly
- Weather integration with provider pattern
- Daily scheduler (cron at 6 AM)
- Push notifications via FCM
- AI advisor daily recommendations

**Infrastructure Verified**
- FastAPI backend with SQLAlchemy ORM
- PostgreSQL database with 9+ core models
- JWT authentication (HS256, 15-min expiry)
- Provider pattern for weather API
- Repository pattern for database access
- Provider state management in Flutter
- Navigation routing in Flutter

---
*No prior changelog entries verified from Git history. This changelog only documents the current documentation generation initiative (2026-11-21).*

---
*Per the documentation quality requirements: "Document only changes verifiable from available Git history or existing changelogs. Do not invent historical releases."*