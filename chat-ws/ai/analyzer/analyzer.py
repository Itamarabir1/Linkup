"""
ניתוח שיחות טרמפ באמצעות AI (Groq API).
"""
import json
from groq import APIError

from .prompts import SYSTEM_PROMPT, USER_PROMPT
from .schema import RideSummary
from .retry import call_api_with_retry


def analyze_ride(chat_text, temperature=0.2):
    """
    מנתח שיחת טרמפ ומחזיר סיכום מובנה בפורמט JSON.
    
    Args:
        chat_text: טקסט השיחה בין נהג לנוסע
        temperature: טמפרטורה למודל (0.0-2.0). ברירת מחדל 0.2 לחילוץ מדויק
        
    Returns:
        JSON string עם פרטי הטרמפ (RideSummary) או הודעת שגיאה
    """
    try:
        user_message = f"{USER_PROMPT}\n\nConversation:\n{chat_text}"
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        # קריאה ל-API עם retry logic
        completion = call_api_with_retry(
            messages=messages,
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=temperature
        )
        
        response_content = completion.choices[0].message.content
        response_json = json.loads(response_content)
        
        # אימות שהתשובה תואמת לסכמה
        ride_summary = RideSummary(**response_json)
        return ride_summary.model_dump_json(indent=2, ensure_ascii=False)
        
    except json.JSONDecodeError as e:
        return f"שגיאה בפענוח JSON: {e}"
    except (APIError, ConnectionError, TimeoutError) as e:
        # שגיאות API אחרי כל הניסיונות
        return f"שגיאה ב-API אחרי ניסיונות חוזרים: {e}"
    except Exception as e:
        return f"שגיאה: {e}"
