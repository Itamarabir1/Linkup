"""
ניתוח batch של כמה שיחות במקביל.
"""
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from .analyzer import analyze_ride
from .schema import RideSummary, BatchRideSummary


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
