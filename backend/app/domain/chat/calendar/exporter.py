"""
ייצוא טרמפים לקובצי iCal (.ics).
"""
from datetime import datetime
from typing import List, Optional

from ..schema_ai import RideSummary
from .calendar import create_calendar_from_rides


def export_to_ical(rides: List[RideSummary], output_path: str, base_date: Optional[datetime] = None) -> bool:
    """
    מייצא רשימת טרמפים לקובץ iCal (.ics).
    
    Args:
        rides: רשימת RideSummary
        output_path: נתיב לקובץ הפלט
        base_date: תאריך בסיס לחישוב תאריכים
        
    Returns:
        True אם הצליח, False אחרת
    """
    try:
        cal = create_calendar_from_rides(rides, base_date)
        
        with open(output_path, 'wb') as f:
            f.write(cal.to_ical())
        
        return True
    except Exception as e:
        print(f"שגיאה ביצירת קובץ לוח שנה: {e}")
        return False


def export_rides_to_ical_bytes(rides: List[RideSummary], base_date: Optional[datetime] = None) -> bytes:
    """
    מייצא רשימת טרמפים ל-bytes של קובץ iCal (.ics).
    
    Args:
        rides: רשימת RideSummary
        base_date: תאריך בסיס לחישוב תאריכים
        
    Returns:
        bytes של קובץ iCal
    """
    from .calendar import create_calendar_from_rides
    cal = create_calendar_from_rides(rides, base_date)
    return cal.to_ical()
