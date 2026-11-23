# AGENTS.md - FarmMate AI

Permanent development instructions for OpenCode agents working on the FarmMate AI project.

---

## 1. Mandatory Project Context

Before starting any development task, read the following documentation in order:

1. **`docs/AI_AGENT_CONTEXT.md`** - Primary project overview, architecture summary, tech stack, feature inventory, data flow, API patterns, database conventions, security requirements, and files to modify casually.

2. **`docs/COMPLETE_FEATURES.md`** - Comprehensive functional documentation of every existing feature, subfeature, workflow, validation, and implementation status. Reference this to understand what exists before adding new features.

3. **`docs/ARCHITECTURE.md`** - Required when making architectural changes. Contains high-level architecture, component interactions, request-response lifecycle, data flow, authentication flow, and Mermaid diagrams.

4. **`docs/DATABASE.md`** - Required before any database changes. Documents all models, tables, fields, relationships, constraints, indexes, migrations, and data access patterns. Includes ER diagram.

5. **`docs/API_DOCUMENTATION.md`** - Required before API changes. Documents all endpoints with HTTP method, URL path, purpose, authentication requirements, request parameters, request body, response structure, status codes, validation, and error responses.

6. **`docs/KNOWN_ISSUES.md`** - Required before bug fixes. Lists confirmed incomplete functionality, existing TODOs, known technical debt, and recommended enhancements.

7. **`docs/FEATURE_MATRIX.md`** - Feature matrix table (Feature × Subfeature × Frontend × Backend × API × Database × Status × Source Files).

8. **Other relevant docs** - Based on the task:
   - `docs/BUSINESS_LOGIC.md` - For business rule changes
   - `docs/ERROR_HANDLING.md` - For error/exception changes
   - `docs/SECURITY.md` - For auth/security changes
   - `docs/PERFORMANCE.md` - For performance-related changes

> **Do not assume documentation overrides actual source code.** Verify important details against current implementations by inspecting the relevant source files.

---

## 2. Development Rules

- **Preserve all existing working functionality.** Never break existing features.
- **Follow the project's established architecture.** The system uses a layered client-server architecture with FastAPI backend and Flutter frontend.
- **Reuse existing services, utilities, and patterns.** Inspect `app/modules/{module}/` for established patterns before creating new code.
- **Avoid unnecessary refactoring.** If it works, don't change it.
- **Do not introduce duplicate features or APIs.** Search existing code before creating new endpoints or screens.
- **Maintain backward compatibility** where required (especially for authentication and API responses).
- **Respect existing authentication and authorization.** All protected endpoints require valid JWT token via `Authorization: Bearer <token>` header. The `get_current_user()` dependency validates the token and checks `is_active`. Farmer profile is required for most operations (checked via `FarmerRepository.get_by_user_id(current_user.id)`).
- **Never expose credentials or secrets.** No hardcoded passwords, API keys in source code.
- **Do not modify unrelated files.** Changes should be scoped to the feature/module being worked on.

---

## 3. Feature Development Workflow

For every new feature, follow these steps:

### Step 1: Understand the Requested Functionality
- Clarify the feature scope and requirements.
- Determine if the feature is truly new or an extension of existing functionality.

### Step 2: Search Existing Documentation
- Read `docs/COMPLETE_FEATURES.md` to check if the feature already exists.
- Read `docs/FEATURE_MATRIX.md` to understand the feature landscape.
- Review `docs/KNOWN_ISSUES.md` to see if this is a known gap.

### Step 3: Inspect the Relevant Source Code
- Examine the appropriate module in `backend/app/modules/{module}/`:
  - `router.py` - API endpoint definitions
  - `service.py` - Business logic
  - `repository.py` - Database access patterns
  - `models.py` - SQLAlchemy model definitions
  - `schemas.py` - Pydantic validation schemas
- For frontend: Examine `mobile/lib/features/{feature_name}/` screens, widgets, and providers.

### Step 4: Identify Affected Components
Determine what needs to change:
- **Backend**: New router, service, repository, models, schemas?
- **Frontend**: New screen, widget, provider?
- **API**: New endpoint path and method?
- **Database**: New table, fields, or constraints?
- **Tests**: New pytest or Flutter test?

### Step 5: Create an Implementation Plan
A concise plan documenting:
- What files will be created/modified.
- Which existing patterns will be reused.
- Potential edge cases and how to handle them.

### Step 6: Implement Using Existing Project Conventions
Follow the project's established patterns:
- **Backend**: FastAPI routes with Pydantic schema validation, SQLAlchemy ORM, repository pattern, JWT authentication.
- **Frontend**: Flutter widgets with Provider state management, Material Design 3 components.
- **API**: Consistent request/response format via `ApiResponse` wrapper.
- **Database**: UUID primary keys, Check Constraints for validation, SQL Enums for status/priority fields.

### Step 7: Add or Update Appropriate Tests
- **Backend**: Add pytest tests in `backend/tests/` following existing patterns in `conftest.py`.
- **Frontend**: Add Flutter widget tests in `mobile/test/` following existing patterns.
- Test new functionality and verify no regressions.

### Step 8: Run Relevant Validation
- Run `pytest` to verify backend changes don't break existing tests.
- Run `flutter test` to verify frontend changes.
- Manually test new API endpoints with `curl` or Postman.
- Verify database migrations work with `alembic upgrade head`.

### Step 9: Update Affected Markdown Documentation
Keep documentation synchronized:
- `COMPLETE_FEATURES.md` - Add new feature with implementation status.
- `FEATURE_MATRIX.md` - Add row for new feature.
- `API_DOCUMENTATION.md` - Add new endpoint documentation.
- `AI_AGENT_CONTEXT.md` - Update feature inventory if relevant.
- **Do not claim features are implemented unless verified** from source code.

### Step 10: Report Implementation Details
Provide a final report including:
- What was implemented or fixed.
- Files created or modified.
- Existing features affected.
- Tests and validation performed.
- Documentation updated.
- Remaining issues or risks.

---

## 4. Bug Fixing Workflow

For every bug, follow these steps:

### Step 1: Reproduce or Investigate the Issue
- Use logs, symptoms, or user reports to understand the bug.
- Check `docs/KNOWN_ISSUES.md` to see if this is a known issue with a workaround.

### Step 2: Identify the Root Cause
- Inspect the relevant source code.
- Trace the error through the service → repository → model layers.
- Check for edge cases that might trigger the bug.

### Step 3: Check Related Known Issues
- Review `docs/KNOWN_ISSUES.md` for similar documented issues.
- Verify the bug isn't a documented trade-off or limitation.

### Step 4: Apply the Smallest Appropriate Fix
- Fix the root cause, not just the symptoms.
- Avoid over-refactoring or changing unrelated parts of the system.
- Use the project's established patterns for error handling and validation.

### Step 5: Test for Regressions
- Run `pytest` to ensure no existing tests break.
- Run `flutter test` to ensure no Flutter tests break.
- Manually test related functionality that might be affected.
- Verify the fix resolves the bug without introducing new issues.

### Step 6: Update Documentation When Behavior Changes
If the bug fix changes any public behavior:
- Update `COMPLETE_FEATURES.md` if feature status changes.
- Update `API_DOCUMENTATION.md` if endpoint responses change.
- Update `BUSINESS_LOGIC.md` if business rules change.
- Update `KNOWN_ISSUES.md` if the issue is now resolved.

---

## 5. Documentation Synchronization

Whenever application behavior changes, update the corresponding documentation in `docs/`.

### Priority Documentation Updates
These four files must be kept synchronized when relevant:

| File | When to Update |
|------|----------------|
| **`COMPLETE_FEATURES.md`** | When a new feature is added, or an existing feature's status changes (IMPLEMENTED → PARTIALLY IMPLEMENTED, etc.). |
| **`FEATURE_MATRIX.md`** | When a new feature/subfeature is added, or status changes. |
| **`API_DOCUMENTATION.md`** | When an API endpoint is added, modified, or removed. |
| **`AI_AGENT_CONTEXT.md`** | When the feature inventory, tech stack, or critical file paths change. |

### Documentation Update Rules
- **Do not claim features are implemented unless verified** from source code.
- **Do not rewrite all documentation unnecessarily.** Only update files that are affected by the change.
- **Preserve existing accurate information.** When updating, keep verified facts and only update what changed.
- **Mark recommendations as proposals, not existing requirements** in `ROADMAP.md`.

### Keeping Documentation Current
After completing any development task, always ask:
1. Does `COMPLETE_FEATURES.md` need an new feature entry?
2. Does `FEATURE_MATRIX.md` need a new row?
3. Does `API_DOCUMENTATION.md` need a new or updated endpoint description?
4. Does `AI_AGENT_CONTEXT.md` need feature inventory or file path updates?

---

## 4. Verification

Before completing any coding task, perform the following verification steps:

### Code Quality Checks
- [ ] Review all changed files for syntax errors.
- [ ] Check for broken imports and references (ensure all imports resolve).
- [ ] Run relevant tests: `pytest` (backend), `flutter test` (frontend).
- [ ] Run static checks when available (black, isort, flake8 for Python; dart format for Dart).
- [ ] Verify existing functionality remains compatible (no regressions).

### Documentation Checks
- [ ] Affected documentation files are updated.
- [ ] No contradictory information across documents.
- [ ] All new features have source file references.
- [ ] Implementation statuses accurately reflect code state.

### Final Checks
- [ ] All imports and references are valid.
- [ ] No secrets or credentials exposed in changed files.
- [ ] Backward compatibility maintained where required.
- [ ] Test results reported (including any that could not be executed).
- [ ] Affected documentation identified and updated.

---

## 5. Final Response Format

For every development task, report the following:

### Implementation Summary
- **What was implemented or fixed.**
- **Files created or modified** (with full paths).
- **Existing features affected** (which features touch or depend on the changes).

### Verification
- **Tests and validation performed** (pytest commands, flutter test commands, manual testing).
- **Documentation updated** (which docs were changed and what was added/modified).
- **Remaining issues or risks** (known limitations, open questions, areas that still need attention).

### Example Response Format

```markdown
## Implementation Summary

**What was implemented or fixed:**
- Brief description of the change.

**Files created or modified:**
- `path/to/file1.py` - Description of changes.
- `path/to/file2.dart` - Description of changes.

**Existing features affected:**
- List of features that depend on or interact with the changed code.

**Tests and validation performed:**
- `pytest` results: summary.
- `flutter test` results: summary.
- Manual testing: brief summary.

**Documentation updated:**
- `docs/COMPLETE_FEATURES.md` - Added new feature X.
- `docs/API_DOCUMENTATION.md` - Added endpoint POST /api/v1/...
- `docs/COMPLETE_FEATURES.md` - Updated feature status.

**Remaining issues or risks:**
- Known limitations, open questions, areas needing future work.
```

---

## Project Knowledge Base

All development decisions should be grounded in the `docs/` directory. The most critical files for context are:

| File | Purpose |
|------|---------|
| `AI_AGENT_CONTEXT.md` | Quick-start context for AI agents (project purpose, architecture, tech stack, feature inventory, data flow, API patterns, security requirements, files to modify casually). |
| `COMPLETE_FEATURES.md` | Every existing feature with implementation status, source file references, and workflows. |
| `ARCHITECTURE.md` | System architecture with Mermaid diagrams (for architectural changes). |
| `DATABASE.md` | Database schemas, models, relationships, constraints, indexes (for database changes). |
| `API_DOCUMENTATION.md` | Complete API endpoint documentation (for API changes). |
| `FEATURE_MATRIX.md` | Feature matrix table (Feature × Subfeature × Frontend × Backend × API × Database × Status × Source Files). |
| `KNOWN_ISSUES.md` | Confirmed incomplete functionality, existing TODOs, known technical debt. |

---

## Quick Reference Commands

### Backend
```bash
cd D:\Projects\Farmate_AI\backend
uv sync                          # Install dependencies
uv run uvicorn app.main:app --reload  # Start dev server (port 8000)
alembic upgrade head             # Apply DB migrations
pytest                           # Run test suite
```

### Frontend
```bash
cd D:\Projects\Farmate_AI\mobile
flutter pub get                  # Install packages
flutter doctor                   # Check environment
flutter run                      # Run on emulator/device
flutter test                     # Run widget/unit tests
```

### Documentation
- All documentation lives in `D:\Projects\Farmate_AI\docs/`
- Primary reference: `AI_AGENT_CONTEXT.md` → `COMPLETE_FEATURES.md` → module-specific docs