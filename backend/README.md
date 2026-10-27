# 🌾 FarmMate AI Backend

AI-powered backend for **FarmMate AI**, a smart farming assistant that helps farmers manage farms, crop seasons, daily activities, weather insights, and AI-powered recommendations.

---

## 🚀 Features

### Authentication

* User Registration
* User Login
* JWT Authentication
* Protected APIs
* User Profile

### Farmer

* Farmer Profile
* Preferred Language
* Farming Experience
* Onboarding

### Farm

* Multiple Farms
* Farm Location
* Land Area
* Soil Type
* Water Source

### Crop Season

* Create Crop Seasons
* Active Crop Management
* Crop Variety
* Sowing & Harvest Dates

### Activities

* Daily Farming Activities
* Irrigation
* Fertilizer
* Weeding
* Pest Control
* Harvest
* Activity Completion Tracking

### Dashboard

* Farmer Summary
* Active Crop
* Today's Activities
* Weather Placeholder
* AI Recommendation Placeholder

### Upcoming Features

* Weather Integration
* Notifications
* AI Recommendations
* AI Chat Assistant
* Simple Analytics
* Disease Detection (Coming Soon)

---

# 🛠 Tech Stack

| Component        | Technology       |
| ---------------- | ---------------- |
| Backend          | FastAPI          |
| Language         | Python 3.13+     |
| Database         | PostgreSQL       |
| ORM              | SQLAlchemy 2.0   |
| Migrations       | Alembic          |
| Validation       | Pydantic v2      |
| Authentication   | JWT              |
| Password Hashing | Passlib (bcrypt) |
| HTTP Client      | httpx            |
| Package Manager  | uv               |

---

# 📁 Project Structure

```text
backend/

app/
├── api/
├── core/
├── database/
├── modules/
│   ├── identity/
│   ├── farmer/
│   ├── farm/
│   ├── crop_season/
│   ├── activity/
│   ├── dashboard/
│   ├── weather/
│   ├── notification/
│   ├── ai/
│   ├── ai_chat/
│   └── analytics/
├── shared/
└── main.py

alembic/
tests/
.env.example
pyproject.toml
uv.lock
README.md
```

---

# ⚙️ Installation

Clone the repository:

```bash
git clone <repository-url>
cd backend
```

Install dependencies:

```bash
uv sync
```

Create a `.env` file:

```env
APP_NAME=FarmMate AI
APP_VERSION=1.0.0
APP_ENV=development

DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/farmmate

JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

AI_API_URL=https://your-provider.example/v1
AI_API_KEY=your-api-key
AI_MODEL=your-model-name
```

The AI client uses one OpenAI-compatible chat-completions endpoint. The three
required values are `AI_API_URL`, `AI_API_KEY`, and `AI_MODEL`; there is no
provider-specific fallback. `AI_API_URL` is the provider base URL (for OmniRoute,
`http://localhost:20128/v1`); the client appends `/chat/completions` unless it is
already present.

Run database migrations:

```bash
uv run alembic upgrade head
```

Start the development server:

```bash
uv run uvicorn app.main:app --reload
```

---

# Push Notifications (Firebase Cloud Messaging)

The backend stores Firebase Installation IDs (FIDs) per farmer and sends
notifications through the Firebase Admin SDK. FCM is transitioning from legacy
registration tokens to FIDs; this project uses the FID APIs.

## Backend configuration

Set one of these environment variables to a Firebase service-account JSON file:

```env
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=/secure/path/farmmate-firebase-service-account.json
# or
GOOGLE_APPLICATION_CREDENTIALS=/secure/path/farmmate-firebase-service-account.json
```

Keep the JSON file outside the repository. If credentials are missing, the API
still starts and notifications are still persisted; push delivery is skipped and
a warning is logged.

Apply the device-registration migration:

```bash
uv run alembic upgrade head
```

## Authenticated endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/notifications/devices` | Register or refresh the current device |
| `DELETE` | `/api/v1/notifications/devices/{fid}` | Remove a device owned by the current farmer |

Registration body:

```json
{
  "fid": "firebase-installation-id",
  "device_name": "Android"
}
```

Registration is idempotent. If the same FID is registered by a different
farmer, ownership moves to the authenticated farmer making the request.

## Delivery behavior

Creating a notification attempts push delivery to every registered FID for that
farmer. Delivery errors are logged but never roll back the persisted
notification. FIDs that FCM reports as unregistered or sender-mismatched are
deleted automatically.

---

# 📚 API Documentation

After starting the server:

* Swagger UI: `http://127.0.0.1:8000/docs`
* ReDoc: `http://127.0.0.1:8000/redoc`

---

# 🧪 Running Tests

```bash
uv run pytest
```

---

# 📦 Current Modules

* ✅ Authentication
* ✅ Farmer
* ✅ Farm
* ✅ Crop Season
* ✅ Activity
* ✅ Dashboard

---

# 🛣 Roadmap

### Version 1.0

* Authentication
* Farmer Management
* Farm Management
* Crop Season
* Activity Management
* Dashboard

### Version 1.1

* Weather Integration
* Notifications
* AI Recommendations
* AI Chat Assistant

### Version 1.2

* Simple Analytics
* Disease Detection

### Future

* Expense Tracking
* Income Tracking
* Financial Reports
* Marketplace
* Community
* Government Schemes

---

# 👨‍💻 Developer

**FarmMate AI Backend**

Built with ❤️ using FastAPI and PostgreSQL.
