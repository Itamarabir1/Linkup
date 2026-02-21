# app/db/base.py
from sqlalchemy.orm import DeclarativeBase

# הגדרת ה-Base המודרנית (SQLAlchemy 2.0 Style)
class Base(DeclarativeBase):
    pass

