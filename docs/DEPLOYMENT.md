# Deployment

## Deployment Overview

FarmMate AI can be deployed using various configurations depending on the environment (development, staging, production).

## Production Deployment Options

### Option 1: Render (Recommended - Already Configured)

The project already includes a `render.yaml` configuration file at the project root.

```yaml
# backend/render.yaml (already exists)
# Defines services for PostgreSQL, Web, and Worker
```

#### Render Setup

1. **Connect GitHub repository** to Render
2. **Create new Web Service** pointing to the repo
3. **Render will auto-detect** the `render.yaml` configuration
4. **Services configured**:
   - **PostgreSQL** database service
   - **Web service** (FastAPI application)
   - **Worker** (if needed for background jobs)

#### Environment Variables on Render

Set these in the Render dashboard for each service:

| Variable | Service | Description |
|----------|-----------|-------------|
| `SECRET_KEY` | Web | JWT signing key |
| `DATABASE_URL` | PostgreSQL + Web | PostgreSQL connection string |
| `APP_ENV` | Web | `production` |
| `ALLOWED_ORIGINS` | Web | Comma-separated list of allowed origins |
| `WEATHER_API_KEY` | Web | Weather provider API key |
| `FIREBASE_PROJECT_ID` | Web | Firebase project ID |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Web | Token expiry (default: 15) |

#### Render URL Format

```
https://farmmate-api-xxx.onrender.com
```

API endpoints would be at:
```
https://farmmate-api-xxx.onrender.com/api/v1/...
```

### Option 2: Docker Deployment

```dockerfile
# Dockerfile for backend
FROM python:3.11-slim

# Install dependencies
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY backend/app /app
WORKDIR /app

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Build and Run

```bash
# Build Docker image
docker build -t farmmate-api .

# Run container
docker run -d \
  -p 8000:8000 \
  -e SECRET_KEY=your-secret-key \
  -e DATABASE_URL=postgresql://user:pass@host:port/db \
  -e APP_ENV=production \
  -e ALLOWED_ORIGINS=https://your-domain.com \
  -e WEATHER_API_KEY=your-key \
  -e FIREBASE_PROJECT_ID=farmmate-ai \
  --name farmmate-api farmmate-api
```

### Option 3: Traditional VPS/Cloud Deployment

```bash
# Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic alembic

# Apply migrations
alembic upgrade head

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Behind reverse proxy (nginx example)
# nginx config would proxy_pass to http://localhost:8000
```

## Database Migration for Production

### Step 1: Create Production Migration

```bash
# From project root
cd D:\Projects\Farmate_AI\backend

# Create new migration
alembic revision --autogenerate -m "Production-ready schema or adjustments"

# Review the generated migration file in alembic/versions/
```

### Step 2: Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Or specific revision
alembic upgrade <revision_id>
```

### Step 3: Verify Database

```bash
# Check table structure
psql $DATABASE_URL -c "\dt"

# Check for any issues
alembic current
```

## Environment Preparation

### Backend `.env` Production Checklist

```
[ ] SECRET_KEY = strong-random-key (32+ chars)
[ ] DATABASE_URL = production PostgreSQL URL
[ ] APP_ENV = production
[ ] ALLOWED_ORIGINS = https://your-domain.com,https://app.your-domain.com
[ ] APP_NAME = FarmMate AI (or keep as is)
[ ] APP_VERSION = 0.1.0 (or semantic version)
[ ] ACCESS_TOKEN_EXPIRE_MINUTES = 15 (or appropriate)
[ ] WEATHER_API_KEY = valid weather provider key
[ ] FIREBASE_PROJECT_ID = firebase project ID
[ ] DEBUG = False (if using any debug settings)
```

### Flutter App Production Checklist

```
[ ] Update api_config.dart base URL to production domain
[ ] Build release APK/IPA: flutter build apk --release
[ ] Configure Firebase for production app
[ ] Set up proper Firebase Cloud Messaging credentials
[ ] Test on real devices (not just emulators)
[ ] Verify HTTPS is working for API calls
```

## Scheduler Configuration in Production

### Daily Job at 6:00 AM

The scheduler is configured to run daily at 6:00 AM:

```python
# From backend/app/modules/scheduler/jobs.py:78-85
scheduler.add_job(
    run_scheduler_job,
    trigger="cron",
    hour=6,
    minute=0,
    id="farmmate_scheduler",
    replace_existing=True,
)
```

### Production Considerations

1. **Multiple instances**: If running multiple backend instances, ensure only one runs the scheduler (or use a distributed scheduler like Celery with Redis)

2. **Cloud Scheduler**: Consider using cloud scheduler services (AWS Event Cron, GCP Cloud Scheduler, etc.) instead of local APScheduler

3. **Error monitoring**: Log scheduler failures to monitoring system (Sentry, CloudWatch, etc.)

4. **Concurrency**: The scheduler has `replace_existing=True` to prevent duplicate jobs on restart

### Disabling Scheduler in Development (with reload)

```python
# From backend/app/modules/scheduler/jobs.py:56-61
# Prevent duplicate scheduler when using uvicorn --reload
if scheduler.running:
    return
```

## API Base URL Configuration

### Development

```
http://127.0.0.1:8000 (or 10.0.2.2:8000 for Android emulator)
```

### Staging

```
https://staging.farmmate.ai/api/v1/...
```

### Production

```
https://farmmate.ai/api/v1/...
# Or whatever domain is configured
```

### Changing the Base URL

Edit `mobile/lib/core/config/api_config.dart`:

```dart
static const baseUrl = 'https://your-production-domain.com';
```

## Monitoring & Logging

### Health Check

```
GET https://your-domain.com/health
# Or: GET /
Returns:
{
  "status": "healthy",
  "application": "FarmMate AI",
  "version": "0.1.0",
  "environment": "production"
}
```

### Logs

- **Uvicorn stdout/stderr**: Default logging output
- **FastAPI /docs**: Auto-generated API documentation at `/docs`
- **Custom logging**: See `ERROR_HANDLING.md` and `LOGGING.md` (if created)

### Recommended Monitoring

- **Uptime**: Monitor server availability
- **Response times**: API performance monitoring
- **Error rates**: Track 4xx/5xx error rates
- **Scheduler status**: Monitor daily job execution
- **FCM delivery**: Monitor push notification delivery rates

## Rollback Procedure

### If Deployment Fails

1. **Identify the issue**: Check logs, error reports
2. **Previous version**: If using Docker, `docker restart previous-image`
3. **Environment rollback**: Revert `.env` changes if needed
4. **Database**: Ensure migrations are reversible (Alembic supports downgrade)
5. **Communication**: Inform users of temporary downtime

```bash
# Docker rollback example
docker stop farmmate-api
docker rm farmmate-api
docker run -d -p 8000:8000 previous-image:tag
```

## Scaling Considerations

### Current Architecture Limitations

1. **Single scheduler instance**: Only one backend process runs the daily job
2. **No distributed caching**: No Redis or Memcached usage
3. **Session stickiness**: JWT tokens are stateless, but farmer profile lookups are not cached
4. **Database connection pooling**: Default SQLAlchemy pooling, may need tuning for high traffic

### Horizontal Scaling Plan

1. **Move scheduler to separate service** or cloud cron
2. **Add Redis** for caching frequently accessed data
3. **Connection pool tuning** in SQLAlchemy `engine` configuration
4. **Stateless API design** already supports horizontal scaling (JWT tokens)
5. **Database read replicas** if read traffic increases significantly

---
*Deployment documentation from codebase analysis as of 2026-11-21. All deployment configs verified from `backend/render.yaml`, `backend/pyproject.toml`, and source code.*