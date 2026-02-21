import logging
from typing import Any, Optional, Dict
from datetime import datetime
# ייבוא השגיאה המותאמת שלך
from app.core.exceptions.handlers import LinkupError

# logger = logging.getLogger(__name__)

# class BaseContextBuilder:
#     """
#     Infrastructure Layer for Context Builders.
#     מכיל כלי עזר לחילוץ נתונים בטוח ולוגיקה ויזואלית משותפת.
#     """
    
#     BASE_URL = "https://itamarabir.com"

#     @classmethod
#     def _resolve_attr(cls, obj: Any, path: str, default: Any = "") -> Any:
#         """
#         Safe Navigation Utility (Deep getattr).
#         """
#         if obj is None:
#             return default
            
#         current = obj
#         for attr in path.split("."):
#             current = getattr(current, attr, None)
#             if current is None:
#                 return default
#         return current

#     @staticmethod
#     def _determine_color(event_key: Optional[str]) -> str:
#         """
#         לוגיקה עסקית להחלטה על צבע ההתראה.
#         """
#         if not event_key:
#             return "green"
            
#         danger_keywords = {"cancel", "reject", "fail", "delete", "stop", "urgent"}
#         event_lower = event_key.lower()
#         if any(word in event_lower for word in danger_keywords):
#             return "red"
            
#         return "green"

#     @staticmethod
#     def _format_date(dt: Any) -> str:
#         """פרמוט תאריך אחיד לכל המערכת"""
#         if isinstance(dt, datetime):
#             return dt.strftime("%d/%m/%Y %H:%M")
#         return str(dt) if dt else "N/A"

# # --- הוספת ה-Facade שיוצא החוצה ---

# class NotificationContext(BaseContextBuilder):
#     """
#     The Facade Class.
#     זהו הקלאס שה-Handler מייבא ומשתמש בו.
#     """

#     @classmethod
#     def build(cls, event_key: str, data: Any) -> Dict[str, Any]:
#         """
#         הפונקציה המרכזית לבניית ה-Context.
#         משתמשת בכלי העזר של BaseContextBuilder ומחזירה מילון מוכן.
#         """
#         try:
#             # בניית הקונטקסט הבסיסי בעזרת כלי העזר של מחלקת האב (Base)
#             context = {
#                 "color": cls._determine_color(event_key),
#                 "timestamp": cls._format_date(datetime.now()),
#                 "base_url": cls.BASE_URL,
#                 "event_key": event_key
#             }

#             # אם הנתונים הם מילון, נמזג אותם פנימה
#             if isinstance(data, dict):
#                 context.update(data)
#             else:
#                 # אם מדובר באובייקט (SQLAlchemy model למשל), ניתן להשתמש ב-_resolve_attr
#                 context["raw_data"] = data

#             return context

#         except Exception as e:
#             logger.error(f"❌ NotificationContext failed for {event_key}: {str(e)}")
#             # שימוש בירושה מ-LinkupError
#             raise LinkupError(
#                 message=f"שגיאה בתהליך הכנת הנתונים להתראה: {event_key}",
#                 status_code=500
#             )

from typing import Any
from .builders.registry import CONTEXT_MAP
from app.core.exceptions.handlers import LinkupError

import logging
from typing import Any, Dict
from .builders.registry import CONTEXT_MAP
from app.domain.notifications.constants import NotificationEvent
from app.core.exceptions.base import LinkupError

logger = logging.getLogger(__name__)

class NotificationContextFacade:
    @classmethod
    def get_context(cls, event_key: NotificationEvent, data: Any) -> Dict[str, Any]:
        config = CONTEXT_MAP.get(event_key)
        if not config:
            raise LinkupError(f"No configuration for event: {event_key}")

        builder = config["builder"]
        schema = config["schema"]

        # ולידציה: אם יש סכמה, נשתמש בה. אם לא, נעביר את האובייקט כמו שהוא.
        processed_data = data
        if schema and isinstance(data, dict):
            processed_data = schema(**data)

        try:
            # הפעלת ה-build (שנשען על ה-BaseBuilder המצוין שלך)
            return builder.build(processed_data, event_key)
        except Exception as e:
            logger.error(f"❌ Builder failed for {event_key}: {e}", exc_info=True)
            raise LinkupError(f"Context construction failed for {event_key}")