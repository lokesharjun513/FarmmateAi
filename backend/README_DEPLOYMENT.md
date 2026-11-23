# FarmMate AI Deployment Readiness

This document outlines the requirements and steps for deploying FarmMate AI to a production environment.

## Required Environment Variables

Before deploying, ensure the following environment variables are set in the production environment (e.g., Render.com Dashboard):

### Application
- `APP_ENV`: Must be set to `production`

### Database
- `DATABASE_URL`: Full PostgreSQL connection string (e.g., `postgresql://user:password@host:port/dbname`)

### JWT
- `JWT_SECRET_KEY`: A strong, randomly generated string for signing JWTs
- `JWT_ALGORITHM`: Usually `HS256`

### AI
- `AI_API_URL`: The API endpoint for the AI provider
- `AI_API_KEY`: Secret API key for the AI provider
- `AI_MODEL`: The specific model to use (e.g., `gpt-4o`)

### Firebase (Optional)
- `FIREBASE_SERVICE_ACCOUNT_KEY_PATH`: Path to the service account JSON file if using Firebase Admin features.

### SMTP
- `SMTP_HOST`: SMTP server address (e.g., `smtp.gmail.com`)
- `SMTP_PORT`: SMTP port (e.g., `587`)
- `SMTP_USER`: SMTP username (e.g., email address)
- `SMTP_PASS`: SMTP app password
- `SMTP_FROM`: From email address

## Deployment Checklist

- [ ] Set `APP_ENV=production`.
- [ ] Ensure `DATABASE_URL` is configured for a secure production database.
- [ ] Ensure `JWT_SECRET_KEY` is a unique, long random string not used elsewhere.
- [ ] Configure `ALLOWED_ORIGINS` with the production URL of the frontend.
- [ ] Ensure SMTP credentials are secure (use App Passwords for Gmail).
- [ ] Verify `render.yaml` settings are appropriate for your specific Render instance.
