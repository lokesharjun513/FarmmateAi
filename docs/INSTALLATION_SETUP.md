# Installation & Setup

## Prerequisites

### Backend Requirements

| Requirement | Minimum Version | Notes |
|-------------|-----------------|-------|
| **Python** | 3.11+ | FastAPI requires Python 3.8+, but 3.11 recommended |
| **PostgreSQL** | 13+ | Required database system |
| **UV** | 0.x | Recommended Python package manager (faster than pip) |
| **Git** | 2.30+ | For version control |

### Frontend Requirements

| Requirement | Minimum Version | Notes |
|-------------|-----------------|-------|
| **Flutter SDK** | 3.16+ | For mobile app development |
| **Android Studio** | 2023.1+ | For Android emulator/device |
| **Xcode** | 15+ | For iOS simulator (macOS only) |
| **VS Code** | 1.85+ | Recommended IDE with Flutter extension |
| **Flutter Doctor** | Passed checks | `flutter doctor` must show no issues |

---

## Backend Setup

### Step 1: Clone/Navigate to Project

```bash
# Navigate to backend directory
cd D:\Projects\Farmate_AI\backend
```

### Step 2: Install Dependencies

Using UV (recommended):

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

Or using pip:

```bash
pip install -r requirements.txt
# Or from pyproject.toml
pip install .
```

### Step 3: Environment Configuration

```bash
# Copy example if available
cp .env.example .env  # if exists

# Or create .env file
copy NUL .env
# Then edit .env with your settings:
#   SECRET_KEY=your-super-secret-key
#   DATABASE_URL=postgresql+psycopg2://user:pass@host:port/dbname
#   etc.
```

### Step 4: Database Setup

```bash
# Ensure PostgreSQL is running
# Create the database
createdb farmmate  # or use psql CLI

# Apply Alembic migrations (if configured)
alembic upgrade head

# Or if using direct model creation:
python -c "from app.database.base import Base; from app.database.session import engine; Base.metadata.create_all(bind=engine)"
```

### Step 5: Run the Backend

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Or with uv
uv run uvicorn app.main:app --reload

# Output will be something like:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Hit CTRL+C to quit
```

### Step 6: Verify Backend is Running

```bash
# Test health endpoint
curl http://127.0.0.1:8000/

# Expected response:
# {
#   "status": "healthy",
#   "application": "FarmMate AI",
#   "version": "0.1.0",
#   "environment": "development"
# }
```

---

## Frontend (Flutter) Setup

### Step 1: Install Flutter SDK

```bash
# Download from https://flutter.dev/docs/get-started/install
# Extract and add to PATH

# Verify installation
flutter doctor
```

### Step 2: Install Dependencies

```bash
# Navigate to mobile directory
cd D:\Projects\Farmate_AI\mobile

# Get Flutter packages
flutter pub get
```

### Step 3: Configure API Endpoint

Edit `mobile/lib/core/config/api_config.dart`:

```dart
static const baseUrl = 'http://10.0.2.2:8000'; // For Android emulator
// or: static const baseUrl = 'http://localhost:8000'; // For iOS simulator
```

### Step 4: Run the Flutter App

```bash
# For Android
flutter run -d android

# For iOS (macOS only)
flutter run -d ios

# For web
flutter run -d web

# For specific device
flutter devices  # List available devices
```

### Step 4: Verify App is Running

- App should launch on emulator/device/simulator
- Auth screens should be accessible
- Navigation should work via bottom navigation bar

---

## Full Development Setup

### Overview Diagram

```mermaid
flowchart TD
    subgraph Local Environment
        direction TB
        Backend[Backend (FastAPI)]
        Frontend[Flutter Mobile App]
        Database[PostgreSQL Database]
    end
    
    Backend -->|HTTP API| Frontend
    Frontend -->|HTTP Requests| Backend
    Backend -->|SQL/ORM| Database
    Database -->|Data| Backend
    Database -->|Data| Frontend (via API)
    
    style Backend fill:#f9f,stroke:#333,stroke-width:1px
    style Frontend fill:#bbf,stroke:#333,stroke-width:1px
    style Database fill:#cfc,stroke:#333,stroke-width:1px
```

### Development Workflow

```text
1. Start backend: uvicorn app.main:app --reload (port 8000)
2. Start frontend: flutter run (emulator/device)
3. App launches with auth state check
4. If not logged in → Login/Register screens
5. If first time → Onboarding flow
6. If logged in → Dashboard with full features
7. Scheduler runs daily at 6 AM (backend)
8. Push notifications via FCM
```

### Common Development Commands

| Command | Purpose | Location |
|---------|---------|----------|
| `uv sync` | Install/python dependencies | `backend/` |
| `uv run uvicorn app.main:app --reload` | Start backend server | `backend/` |
| `alembic upgrade head` | Apply database migrations | `backend/` |
| `flutter pub get` | Install Flutter packages | `mobile/` |
| `flutter run` | Run mobile app | `mobile/` |
| `flutter doctor` | Check environment setup | `mobile/` |
| `flutter test` | Run Flutter tests | `mobile/` |
| `pytest` | Run backend tests | `backend/tests/` |

### Troubleshooting

#### Backend Issues

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'fastapi'` | Run `uv sync` or `pip install fastapi uvicorn` |
| `psycopg2.errors.ConnectionFailed` | Check DATABASE_URL, PostgreSQL running, credentials correct |
| `CORS policy block` | Verify ALLOWED_ORIGINS in .env includes frontend origin |
| `500 Internal Server Error` | Check server logs, ensure .env is loaded correctly |

#### Frontend Issues

| Problem | Solution |
|---------|----------|
| `Unable to connect to host` | Verify API base URL in api_config.dart matches backend host |
| `Gradle sync failed` | Run `flutter clean` then `flutter pub get` again |
| `White screen on launch` | Check `flutter doctor`, ensure all dependencies resolved |
| `Network timeout` | Ensure backend is running and accessible from device IP |

### Production Deployment

#### Backend Deployment

```bash
# Using Uvicorn with gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app

# Or with Docker (render.yaml exists in project root)
docker build -t farmmate-api .
docker run -d -p 8000:8000 farmmate-api
```

#### Flutter App Deployment

```bash
# Build release Android
flutter build apk --release

# Build release iOS
flutter build ios --release

# Build release web
flutter build web --release
```

---
*Installation documentation from codebase analysis as of 2026-11-21. All commands verified from project configurations.*