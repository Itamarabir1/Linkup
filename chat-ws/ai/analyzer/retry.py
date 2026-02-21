"""
לוגיקת retry ו-exponential backoff לקריאות API.
"""
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from groq import APIError

from .client import client


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
def call_api_with_retry(messages, model, response_format, temperature):
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
