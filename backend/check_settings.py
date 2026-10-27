from app.core.config import settings

print(f"AI_API_URL: {settings.AI_API_URL}")
print(f"AI_API_KEY: {settings.AI_API_KEY.get_secret_value()}")
print(f"AI_MODEL: {settings.AI_MODEL}")
