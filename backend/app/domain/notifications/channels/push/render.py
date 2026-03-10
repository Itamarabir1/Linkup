import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def render_push_content(template_config: dict, **context) -> tuple[str, str]:
    """
    מבצע רינדור בטוח לכותרת ולגוף של התראת הפוש.
    """
    # 1. שליפת התבניות
    title_tpl = template_config.get("title", "עדכון מ-LinkUp")
    body_tpl = template_config.get("body", "")

    try:
        # 2. הקסם הסניורי: Safe Formatting
        # אנחנו יוצרים "מילון חכם" שמונע KeyErrors.
        # אם חסר מפתח, הוא פשוט לא יציג כלום (או יציג סימן שאלה) במקום לקרוס.
        safe_context = defaultdict(lambda: "", **context)

        final_title = title_tpl.format_map(safe_context)
        final_body = body_tpl.format_map(safe_context)

        return final_title.strip(), final_body.strip()

    except Exception as e:
        # הגנה אחרונה למקרה של שגיאות תחביר בתבנית עצמה (כמו סוגריים לא סגורים)
        logger.error(f"❌ Critical Error rendering push: {e}")
        return title_tpl, body_tpl
