# Development Guide

## Coding Conventions

### Python (Backend)

#### File Organization
- Each module has its own `router.py`, `service.py`, `models.py`, `schemas.py`, `repository.py`
- Import ordering: FastAPI → SQLAlchemy → local modules → shared
- Type hints required for all function signatures
- Docstrings for all public functions (numpy/docstring format recommended)

#### Naming Conventions
- **Functions**: `snake_case` (e.g., `create_farm_endpoint`, `get_current_user`)
- **Classes**: `PascalCase` (e.g., `FarmerRepository`, `CropSeasonService`)
- **Variables**: `snake_case` (e.g., `farmer_id`, `crop_name`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_COUNT`)
- **Enum values**: UPPER_SNAKE_CASE (e.g., `CropSeasonStatus.PLANNED`)
- **File names**: `snake_case` (e.g., `farmer_router.py`, `crop_stage_models.py`)

#### Code Style
- Black formatter for code formatting
- isort for import ordering
- Flake8 for linting
- Type checking with mypy (optional but recommended)

#### Example Function Pattern

```python
def create_farm_endpoint(
    request: FarmCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[FarmResponse]:
    """Create a new farm for the authenticated farmer."""
    
    # Get farmer profile (required for farm operations)
    farmer_repository = FarmerRepository(db)
    farmer = farmer_repository.get_by_user_id(current_user.id)
    
    if farmer is None:
        raise FarmerProfileNotFoundError()
    
    # Create farm via service
    farm_repository = FarmRepository(db)
    farm = create_farm(
        repository=farm_repository,
        farmer_id=farmer.id,
        request=request,
    )
    
    return ApiResponse(
        success=True,
        message="Farm created successfully.",
        data=FarmResponse.model_validate(farm),
    )
```

### Dart (Frontend)

#### File Organization
- Feature modules in `lib/features/{feature_name}/`
- Presentation layer: screens + widgets
- Data layer: models + repositories + providers
- Consistent import paths from `lib/core/`, `lib/shared/`

#### Naming Conventions
- **Widgets**: `PascalCase` (e.g., `AddFarmForm`, DashboardScreen`)
- **Screens**: `PascalCase` with `Screen` suffix (e.g., `ProfileScreen`)
- **Providers**: `*_provider.dart` suffix (e.g., `farmer_provider.dart`)
- **Models**: `*_model.dart` suffix (e.g., `farm_model.dart`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_LINE_LENGTH`)
- **Functions**: `camelCase` (e.g., `calculateCropAge`)
- **Variables**: `camelCase` (e.g., `cropAgeDays`)

#### Example Widget Pattern

```dart
class AddFarmForm extends StatefulWidget {
  const AddFarmForm({super.key, required this.onFarmCreated});

  final VoidCallback onFarmCreated;

  @override
  State<AddFarmForm> createState() => _AddFarmFormState();

  static _AddFarmState createState() =>
      _AddFarmFormState(); // For testing
}

class _AddFarmFormState extends State<AddFarmForm> {
  final _formKey = GlobalKey<FormState>();
  final _farmNameController = TextEditingController();
  final _landAreaController = TextEditingController();
  // ... other controllers
  
  @override
  void dispose() {
    _farmNameController.dispose();
    _landAreaController.dispose();
    // ... dispose all controllers
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        children: [
          TextFormField(
            controller: _farmNameController,
            decoration: const InputDecoration(
              labelText: 'Farm Name',
              border: OutlineInputBorder(),
            ),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Please enter farm name';
              }
              return null;
            },
          ),
          // ... more form fields
          ElevatedButton(
            onPressed: () {
              if (_formKey.currentState!.validate()) {
                _createFarm();
              }
            },
            child: const Text('Create Farm'),
          ),
        ],
      ),
    );
  }
  
  Future<void> _createFarm() async {
    // Validate and submit farm creation
    final response = await http.post(
      Uri.parse('${ApiConfig.baseUrl}/api/v1/farms'),
      headers: {
        'Authorization': 'Bearer ${AuthProvider.token}',
        'Content-Type': 'application/json',
      },
      body: json.encode({
        'farm_name': _farmNameController.text,
        'land_area': double.tryParse(_landAreaController.text) ?? 0,
        // ... other fields
      }),
    );
    
    if (response.statusCode == 201) {
      widget.onFarmCreated();
      Navigator.of(context).pop();
    } else {
      // Show error
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to create farm')),
      );
    }
  }
}
```

## Database Migration Guidelines

### Adding New Models

1. **Add model** to `backend/app/database/models.py` OR create module-level models
2. **Add Alembic migration**:
   ```bash
   alembic revision --autogenerate -m "Add new model"
   ```
3. **Apply migration**:
   ```bash
   alembic upgrade head
   ```
4. **Update repositories** if needed (new repository methods)
5. **Update schemas** if API exposure needed

### Changing Existing Models

1. **Modify model fields** in the appropriate model file
2. **Create new migration** for non-backward-compatible changes
3. **Test existing queries** still work
4. **Update repository methods** if query patterns change

### Migration Commands

```bash
# Create new migration
alembic revision --autogenerate -m "Descriptive message about changes"

# List migrations
alembic list

# View migration head
alembic heads

# Downgrade one step
alembic downgrade -1

# Current revision
alembic current
```

## API Development Guidelines

### Adding New Endpoints

1. **Add route** to module's `router.py`
2. **Create service function** in module's `service.py`
3. **Add repository method** in module's `repository.py` (if DB operation)
4. **Add Pydantic schema** in module's `schemas.py` (request/response)
5. **Register router** in `backend/app/api/v1/router.py` (if new module)
6. **Add tests** in `backend/tests/` directory
7. **Update API documentation** in `docs/API_DOCUMENTATION.md`

### Request Validation

- All request bodies validated via Pydantic schemas
- Query parameters validated via FastAPI `Query()` or `Optional[]`
- Path parameters typed appropriately (e.g., `farm_id: UUID`)
- Response models defined via `response_model` parameter

### Response Format

```python
# Standard success response
return ApiResponse(
    success=True,
    message="Operation completed successfully.",
    data=response_model_instance,
)

# Error responses raise HTTPExceptions
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Farmer profile not found.",
)
```

## Testing Guidelines

### Backend Tests (Pytest)

#### Test Structure

```python
# Example test file: backend/tests/test_farmer.py

def test_create_farmer_profile(db_session, new_user):
    """Test farmer profile creation."""
    from app.modules.farmer.service import create_farmer_profile
    from app.modules.farmer.schemas import FarmerCreateRequest
    
    # Arrange
    request = FarmerCreateRequest(
        preferred_language="English",
        experience_years=5,
    )
    
    # Act
    result = create_farmer_profile(
        repository=FarmerRepository(db_session),
        user_id=new_user.id,
        request=request,
    )
    
    # Assert
    assert result.success == True
    assert result.data is not None
    assert result.data.profile_completion == 0
    assert result.data.onboarding_completed == False
```

#### Test Fixtures (conftest.py)

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def engine():
    return create_engine("sqlite:///:memory:")

@pytest.fixture
def session(engine):
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def new_user(session):
    from app.modules.identity.models import User
    from app.shared.mixins import TimestampMixin
    
    user = User(
        full_name="Test User",
        mobile="+919876543210",
        email="test@example.com",
        password_hash="hashed_password",
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
```

### Flutter Tests

```dart
// Example test
void main() {
  group('Auth Provider', () {
    test('can init login', () {
      final provider = AuthProvider();
      expect(provider.isLoggedIn, isFalse);
    });
    
    test('can set logged in', () {
      final provider = AuthProvider();
      provider.login();
      expect(provider.isLoggedIn, isTrue);
    });
  });
}
```

### Test Categories

| Category | Scope | Location |
|----------|-------|----------|
| Unit tests | Individual functions/services | `backend/tests/test_*.py` |
| Integration tests | API endpoints with DB | `backend/tests/` |
| Widget tests | Flutter widget behavior | `mobile/test/` |
| Feature tests | End-to-end user flows | Could be in either |

## Debugging & Logging

### Backend Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log messages at appropriate levels
logger.debug("Debug message")
logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error message")
logger.exception("Exception with stack trace")

# Used throughout codebase:
# - scheduler/jobs.py: logger.info("Scheduler completed successfully")
# - scheduler/service.py: logger.exception("Advisor generation failed")
# - main.py: logger.info("Scheduler started successfully")
```

### Common Debug Patterns

1. **Check FastAPI auto-docs**: `http://127.0.0.1:8000/docs`
2. **Health check**: `http://127.0.0.1:8000/`
3. **Test endpoints**: Use `curl` or Postman
4. **View logs**: Console output from uvicorn
5. **Database queries**: Use pgAdmin or psql to inspect data

### Flutter Debugging

```bash
# Show debug console output
flutter run -v

# Add debug print statements
print('Debug: variable value = $value');

# Use Dart observatory
flutter run -c  # Hot reload with debug options

# Check system messages
adb logcat | grep -i flutter
```

## Project Structure Responsibilities

### Backend Directories

| Directory | Responsibility |
|-----------|---------------|
| `app/main.py` | App entry point, middleware, lifecycle |
| `app/api/v1/router.py` | Router registration, module inclusion |
| `app/core/` | Core configuration, auth, exceptions, middleware |
| `app/database/` | SQLAlchemy models, session management |
| `app/modules/{module}/` | Module-specific logic (service, repository, models, schemas) |
| `app/shared/` | Shared utilities, enums, constants, exceptions |
| `app/tests/` | Pytest test files and fixtures |

### Frontend Directories

| Directory | Responsibility |
|-----------|---------------|
| `mobile/lib/main.dart` | App entry point, router, theme initialization |
| `lib/app/` | App-wide configuration (theme, router) |
| `lib/core/` | Core utilities (storage, network, location, config) |
| `lib/features/{feature}/` | Feature modules (auth, farmer, farm, dashboard, etc.) |
| `lib/shared/widgets/` | Reusable UI widgets (ai_greeting_card, ai_chat_bubble) |
| `lib/shared/theme/` | App theming (colors, typography) |
| `lib/shared/router/` | Navigation routing configuration |

## Common Development Commands Summary

```bash
# Backend
cd D:\Projects\Farmate_AI\backend
uv sync                          # Install dependencies
uv run uvicorn app.main:app --reload  # Start dev server
alembic upgrade head             # Apply migrations
pytest                           # Run tests

# Frontend
cd D:\Projects\Farmate_AI\mobile
flutter pub get                  # Install packages
flutter doctor                   # Check environment
flutter run                      # Run app on device/emulator
flutter test                     # Run widget/unit tests
flutter build apk --release      # Build release APK
```

---
*Development guide from codebase analysis as of 2026-11-21. All conventions and patterns verified from actual source code.*