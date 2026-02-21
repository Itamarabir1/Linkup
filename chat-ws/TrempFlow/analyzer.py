import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from groq import APIError
from client import client
from prompts import SYSTEM_PROMPT, USER_PROMPT
from schema import RideSummary, BatchRideSummary


def _is_retryable_error(exception):
    """
    בודק אם שגיאה היא מסוג שניתן לנסות שוב.
    
    שגיאות שניתן לנסות שוב:
    - Network errors (connection errors)
    - Rate limits (429)
    - Server errors (500-599)
    
    שגיאות שלא כדאי לנסות שוב:
    - Validation errors (400)
    - Authentication errors (401)
    - JSON parsing errors
    """
    if isinstance(exception, APIError):
        # Rate limit או server error - ניתן לנסות שוב
        if exception.status_code in [429, 500, 502, 503, 504]:
            return True
        # Validation או authentication - לא לנסות שוב
        if exception.status_code in [400, 401, 403]:
            return False
    
    # Network errors - ניתן לנסות שוב
    if isinstance(exception, (ConnectionError, TimeoutError)):
        return True
    
    # שגיאות אחרות - לא לנסות שוב
    return False


@retry(
    stop=stop_after_attempt(3),  # מנסה עד 3 פעמים
    wait=wait_exponential(multiplier=1, min=1, max=10),  # 1s, 2s, 4s
    retry=retry_if_exception(_is_retryable_error),  # מנסה שוב רק אם השגיאה היא retryable
    reraise=True  # מעלה את השגיאה אחרי כל הניסיונות
)
def _call_api_with_retry(messages, model, response_format, temperature):
    """
    קורא ל-API עם retry logic ו-exponential backoff.
    
    Args:
        messages: רשימת הודעות למודל
        model: שם המודל
        response_format: פורמט התשובה
        temperature: טמפרטורה
        
    Returns:
        התשובה מה-API
        
    Raises:
        APIError: אם כל הניסיונות נכשלו
    """
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format=response_format,
        temperature=temperature
    )
    return completion


# פונקציה שמקבלת שיחה ומחזירה סיכום שלה 
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
        completion = _call_api_with_retry(
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


def analyze_rides_batch(chat_texts: List[str], temperature=0.2, max_workers=5) -> BatchRideSummary:
    """
    מנתח כמה שיחות טרמפ במקביל (parallel) ומחזיר batch של תוצאות.
    
    Args:
        chat_texts: רשימה של טקסטי שיחות
        temperature: טמפרטורה למודל
        max_workers: כמה שיחות לשלוח במקביל (default: 5)
        
    Returns:
        BatchRideSummary עם כל התוצאות
    """
    rides = []
    
    # שולח את כל השיחות במקביל
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # שולח את כל המשימות
        future_to_chat = {
            executor.submit(analyze_ride, chat_text, temperature): chat_text 
            for chat_text in chat_texts
        }
        
        # אוסף את התוצאות כשהן מגיעות
        for future in as_completed(future_to_chat):
            try:
                result_json = future.result()
                # ממיר את ה-JSON string חזרה לאובייקט
                result_dict = json.loads(result_json)
                ride_summary = RideSummary(**result_dict)
                rides.append(ride_summary)
            except Exception as e:
                # אם יש שגיאה, מדלג על השיחה הזו
                print(f"שגיאה בעיבוד שיחה: {e}")
                continue
    
    return BatchRideSummary(rides=rides)
