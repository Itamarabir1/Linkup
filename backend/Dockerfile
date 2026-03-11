FROM python:3.11-slim

# הגדרת תיקיית העבודה בתוך הקונטיינר
WORKDIR /app

# התקנת תלויות מערכת שדרושות ל-PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# העתקת הגדרת הפרויקט והתקנת תלויות עם uv
COPY pyproject.toml .
RUN pip install uv && uv pip install --system -e .

# העתקת שאר הקוד
COPY . .

# הרצת השרת
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]