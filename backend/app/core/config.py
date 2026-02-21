from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, EmailStr, computed_field
from functools import lru_cache
from typing import Optional, Dict, Any, List

# תיקיית backend (היכן ש-.env נמצא) – כך שה-.env נטען גם כשמריצים מ-cwd אחר
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    """
    LinkUp System Settings - Architect Edition (2026).
    ניהול ריכוזי של כל משתני הסביבה עם וולידציה בזמן עלייה.
    מעודכן לתמיכה ב-Kafka KRaft וארכיטקטורת אירועים מלאה.
    """
    
    # --- Project Metadata ---
    PROJECT_NAME: str = "LinkUp"
    APP_NAME: str = "linkup-backend"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # --- PostgreSQL / PostGIS ---
    POSTGRES_USER: str = Field("admin")
    POSTGRES_PASSWORD: str = Field("password123")
    POSTGRES_DB: str = Field("linkup_app")
    POSTGRES_HOST: str = Field("localhost")
    POSTGRES_PORT: str = Field("5432")

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # --- Redis ---
    REDIS_HOST: str = Field("localhost")
    REDIS_PORT: int = Field(6379)
    REDIS_DB: int = Field(0)
    REDIS_PASSWORD: Optional[str] = Field(None)

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # --- RabbitMQ (Infrastructure & Celery) ---
    RABBITMQ_HOST: str = Field("localhost")
    RABBITMQ_PORT: int = Field(5672)
    RABBITMQ_USER: str = Field("guest")
    RABBITMQ_PASSWORD: str = Field("guest")
    CELERY_TIMEZONE: str = Field("Asia/Jerusalem")

    @computed_field
    @property
    def RABBITMQ_URL(self) -> str:
        """המקור היחיד לאמת עבור RabbitMQ - משמש את ה-Client ואת Celery"""
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"

    @computed_field
    @property
    def CELERY_BROKER_URL(self) -> str:
        return self.RABBITMQ_URL

    # --- Kafka (KRaft Mode - No Zookeeper) ---
    KAFKA_BOOTSTRAP_SERVERS: str = Field("localhost:9092")
    
    # Topics
    KAFKA_TOPIC_RIDES: str = Field("rides_stream")
    KAFKA_TOPIC_NOTIFICATIONS: str = Field("user_notifications")
    KAFKA_TOPIC_AUTH: str = Field("auth_events")
    KAFKA_TOPIC_ANALYTICS: str = Field("system_analytics")

    @computed_field
    @property
    def KAFKA_PRODUCER_CONFIG(self) -> Dict[str, Any]:
        """קונפיגורציה מוכנה להזרקה ל-AIOKafkaProducer"""
        return {
            "bootstrap_servers": self.KAFKA_BOOTSTRAP_SERVERS,
            "acks": "all",
            "retry_backoff_ms": 100,
        }

    # --- Frontend & API (לינקים במיילים / כפתורים) ---
    FRONTEND_URL: str = Field(
        "https://linkup.co.il",
        description="כתובת האפליקציה (פרונט). מפנה הצלחה/שגיאה אחרי אימות.",
    )
    API_PUBLIC_URL: str = Field(
        "",
        description="כתובת הבקאנד בציבור (למשל https://api.linkup.co.il). אם מוגדר – כפתור אימות במייל יפתח לינק אימות בלחיצה אחת.",
    )

    # --- External Services (Brevo / Sendinblue) ---
    BREVO_API_KEY: str = Field("")
    BREVO_SENDER_EMAIL: EmailStr = Field("support@itamarabir.com")
    BREVO_SENDER_NAME: str = Field("LinkUp", description="שם השולח במיילים")

    # --- EIA (U.S. fuel prices API) ---
    # Get free API key: https://www.eia.gov/opendata/register.php
    EIA_API_KEY: str = Field("", description="EIA Open Data API key for fuel price scanner")
    
    # --- Google Maps Geocoding API ---
    GOOGLE_MAPS_API_KEY: str = Field(
        "",
        description="Google Maps API key – Geocoding, Directions, Distance Matrix. גם נשלח לפרונט ל-Maps JavaScript API דרך GET /api/v1/geo/maps-key.",
    )

    # --- Google OAuth ---
    GOOGLE_CLIENT_ID: str = Field(
        "",
        description="Google OAuth 2.0 Client ID מה-Google Cloud Console. נדרש לאימות ID tokens מ-Google Sign-In.",
    )
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(
        None,
        description="Google OAuth 2.0 Client Secret (אופציונלי - נדרש רק אם צריך access tokens, לא ל-ID token verification).",
    )

    # --- Security & Auth (חובה בפרודקשן – בפיתוח ברירת מחדל) ---
    SECRET_KEY: str = Field("dev-secret-key-change-in-production", description="Must be set in .env for production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, description="תוקף Access Token בדקות")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, description="תוקף Refresh Token בימים (לטוקן הארוך)")
    JWT_ISSUER: str = Field("linkup-api", description="JWT claim 'iss' (issuer)")

    # --- HTTPS (פרודקשן מאחורי Proxy) ---
    FORCE_HTTPS_REDIRECT: bool = Field(
        False,
        description="If True, redirect HTTP requests to HTTPS (set when behind a proxy that sets X-Forwarded-Proto).",
    )

    # --- CORS ---
    CORS_ORIGINS: List[str] = Field(
        default_factory=list,
        description="Allowed CORS origins. If empty, FRONTEND_URL is used.",
    )

    # --- Rate limiting (auth endpoints) ---
    RATE_LIMIT_AUTH_WINDOW_SECONDS: int = Field(60, description="חלון זמן ל-rate limit על auth (שניות)")
    RATE_LIMIT_AUTH_MAX_REQUESTS: int = Field(10, description="מקסימום בקשות ל-auth ל-IP בחלון")

    # --- Cloud Infrastructure (AWS & Firebase) – אופציונלי בפיתוח ---
    AWS_ACCESS_KEY_ID: str = Field("")
    AWS_SECRET_ACCESS_KEY: str = Field("")
    AWS_REGION: str = "eu-central-1"
    S3_BUCKET_NAME: str = Field("")

    # --- Upload temp directory (קבצים זמניים לפני העלאה ל-S3) ---
    # ברירת מחדל: תיקיית המערכת (tempfile.gettempdir()). אם מוגדר – משתמשים בתיקייה זו (נוצר אוטומטית אם חסר).
    UPLOAD_TEMP_DIR: Optional[str] = Field(
        None,
        description="Optional directory for upload temp files; default is system temp.",
    )

    FIREBASE_SERVICE_ACCOUNT_PATH: str = Field("", description="Path to Firebase JSON (optional for local dev)")

    # --- Pydantic Configuration ---
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()