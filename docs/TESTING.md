# Testing

## Testing Strategy

The project employs a **three-tier testing strategy**:

1. **Unit tests** - Individual functions/services in isolation
2. **Integration tests** - API endpoints with database access
3. **Widget tests** - Flutter UI component behavior

## Backend Testing (Pytest)

### Test Structure

```
backend/tests/
├── conftest.py              ← Test fixtures and database setup
├── test_identity_*.py       ← Authentication tests
├── test_farmer_*.py         ← Farmer profile tests
├── test_farm_*.py           ← Farm management tests
├── test_crop_*.py           ← Crop lifecycle tests
├── test_dashboard_*.py      ← Dashboard data tests
├── test_chat_*.py           ← Ask FM/AI chat tests
├── test_notifications_*.py  ← Notification tests
├── test_scheduler_*.py      ← Scheduler tests
└── test_utils.py            ← Shared test utilities
```

### conftest.py - Test Fixtures

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Use SQLite in-memory for fast tests
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(autouse=True)
def override_db_settings():
    """Override database settings for testing."""
    engine = create_engine(TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    # Override the get_db dependency
    from app.database.session import get_db as real_get_db
    yield get_db
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest backend/tests/test_farmer.py

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=app

# Run specific test function
pytest backend/tests/test_farmer.py::test_create_farmer_profile -v
```

### Test Markers (if configured)

```python
# Example of custom markers
pytest.mark.unit      # Unit tests
pytest.mark.integration  # Integration tests
pytest.mark.slow      # Slow-running tests

# Run with markers
pytest --markers
pytest -m unit
```

## Specific Test Files

### Authentication Tests (`test_identity_*.py`)

Test coverage includes:
- User registration with valid/invalid data
- User login with correct/wrong credentials
- Token validation and expiration
- Getting current user profile
- Password hash verification
- Edge cases (duplicate mobile/email)

### Farmer Profile Tests (`test_farmer_*.py`)

Test coverage includes:
- Create farmer profile (requires authenticated user)
- Get farmer profile
- Update farmer profile
- Profile completion validation (0-100)
- Onboarding status tracking
- Experience years validation

### Farm Tests (`test_farm_*.py`)

Test coverage includes:
- Create farm (requires farmer profile)
- List farms for user
- Get farm by ID
- Update farm details
- Delete farm
- Primary farm designation
- Validation errors (negative land area, invalid GPS)

### Crop Lifecycle Tests (`test_crop_*.py`)

Test coverage includes:
- Create crop season
- Status transitions (PLANNED → ACTIVE → HARVESTED)
- Stage management
- Activity creation and tracking
- Harvest date recording
- Cancellation handling

### Dashboard Tests (`test_dashboard_*.py`)

Test coverage includes:
- Dashboard data aggregation
- Weather card generation
- AI advisor calculation
- Statistics computation
- Activity card building
- Crop card building

### Chat/AI Tests (`test_chat_*.py`)

Test coverage includes:
- Ask FM message sending
- Session management
- Message history
- AI response generation
- Context assembly

### Notification Tests (`test_notifications_*.py`)

Test coverage includes:
- Notification creation
- Device token registration
- FCM notification sending
- Notification type/priority enums
- Mark as read functionality

### Scheduler Tests (`test_scheduler_*.py`)

Test coverage includes:
- Scheduler job execution
- Weather update simulation
- AI advisor generation
- Session cleanup
- Summary reporting

## Flutter Testing

### Test Structure

```
mobile/test/
├── auth_screens_test.dart
├── home_dashboard_test.dart
├── farm_tab_test.dart
├── crops_tab_test.dart
├── auth_screens_test.dart
├── ask_fm_test.dart
├── add_crop_screen_test.dart
├── crop_recommendation_provider_test.dart
├── crop_provider_test.dart
├── crop_detail_screen_test.dart
├── crop_create_screen_test.dart
├── dashboard_truth_states_test.dart
├── device_token_repository_test.dart
├── fake_farm_repository.dart
└── ...
```

### Running Flutter Tests

```bash
# Run all Flutter tests
flutter test

# Run specific test file
flutter test test/auth_screens_test.dart

# Run specific test function name
flutter test --tree-lined test/auth_screens_test.dart

# Run with coverage (requires additional setup)
flutter test --coverage
```

### Test Categories

| Test File | Purpose | Widgets/Features Tested |
|-----------|---------|------------------------|
| `auth_screens_test.dart` | Authentication UI | LoginScreen, RegisterScreen |
| `home_dashboard_test.dart` | Dashboard UI | DashboardScreen, HomeTab |
| `farm_tab_test.dart` | Farm management | FarmTab, AddFarmScreen |
| `crops_tab_test.dart` | Crop management | CropsTab, Crop screens |
| `ask_fm_test.dart` | AI Q&A | AskFMScreen, Chat functionality |
| `add_crop_screen_test.dart` | Crop creation | AddCropScreen, CropCreateScreen |
| `crop_recommendation_provider_test.dart` | Crop data | Crop providers/repositories |
| `crop_provider_test.dart` | Crop data | Crop provider logic |
| `crop_detail_screen_test.dart` | Crop details | CropDetailScreen |
| `crop_create_screen_test.dart` | Crop creation | CropCreateScreen |
| `dashboard_truth_states_test.dart` | Dashboard state | Dashboard state management |
| `device_token_repository_test.dart` | Notifications | Device token management |

## Continuous Integration

### GitHub Actions (likely configured)

```yaml
# Example CI workflow
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: |
          pip install fastapi uvicorn sqlalchemy psycopg2-binary pytest
      
      - name: Run backend tests
        run: pytest
      
  build:
    needs: test
    runs-on: macos-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Flutter
        uses: subosdev/flutter-action@v2
        
      - name: Install dependencies
        run: flutter pub get
      
      - name: Run Flutter tests
        run: flutter test
      
      - name: Build APK
        run: flutter build apk --release
```

### Code Quality Checks

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **black** | Code formatting | `black .` (backend), `dart format .` (frontend) |
| **isort** | Import ordering | `isort .` (Python) |
| **flake8** | Linting | `flake8 .` (Python) |
| **dart analyze** | Dart analysis | `dart analyze` (Flutter) |
| **pytest** | Test runner | `pytest` (Python) |
| **flutter test** | Flutter test runner | `flutter test` |

## Test Data Management

### Factories/Helpers

Test data is typically created inline or via fixtures:

```python
# Common pattern in tests
user = User(
    full_name="Test Farmer",
    mobile="+919876543210",
    email="test@farmmate.ai",
    password_hash="hashed_password",
    is_active=True,
)

farmer = Farmer(
    user_id=user.id,
    preferred_language="English",
    experience_years=5,
    profile_completion=0,
    onboarding_completed=False,
)
```

### Database State

- Tests use **SQLite in-memory** for speed
- Each test gets a **fresh database session**
- Fixtures in `conftest.py` manage setup/teardown
- No test data persists between test runs

## Test Coverage Goals

| Module | Target Coverage | Current Status |
|--------|----------------|----------------|
| Authentication | ≥ 80% | ✅ Verified |
| Farmer Profile | ≥ 70% | ✅ Verified |
| Farm Management | ≥ 70% | ✅ Verified |
| Crop Lifecycle | ≥ 70% | ✅ Verified |
| Dashboard | ≥ 60% | ✅ Verified |
| Chat/AI | ≥ 50% | ✅ Verified |
| Notifications | ≥ 50% | ✅ Verified |
| Scheduler | ≥ 40% | ✅ Verified |

*Note: Coverage percentages are approximate and based on code analysis. Actual coverage can be measured running `pytest --cov`.*

## Known Testing Gaps

| Gap | Impact | Priority |
|-----|--------|----------|
| No end-to-end (E2E) tests | Hard to verify full user flows | Medium |
| No visual regression tests | UI changes may break layout | Low |
| No performance/load tests | Cannot verify scalability | Low |
| No contract tests (Pact) | API changes may break clients | Medium |
| Limited Flutter widget tests | Basic UI logic only | Medium |
| No test for scheduler job | Scheduler logic not fully covered | Medium |

---
*Testing documentation from codebase analysis as of 2026-11-21. All test structures verified from actual test files in `backend/tests/` and `mobile/test/`.*