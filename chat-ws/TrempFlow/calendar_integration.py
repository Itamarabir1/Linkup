"""
מודול לאינטגרציה עם לוח שנה
מייצר קבצי iCal (.ics) שניתן לייבא לכל יישום לוח שנה
"""
from datetime import datetime, timedelta
from typing import Optional, List
from icalendar import Calendar, Event
from schema import RideSummary, BatchRideSummary
import re


def parse_hebrew_time(time_str: str, base_date: Optional[datetime] = None) -> Optional[datetime]:
    """
    מפרסר זמן בעברית (למשל "08:00", "16:00", "מחר ב-08:00") לאובייקט datetime.
    
    Args:
        time_str: מחרוזת זמן בעברית
        base_date: תאריך בסיס לחישוב (אם לא מוגדר, משתמש בתאריך הנוכחי)
        
    Returns:
        datetime object או None אם לא ניתן לפרסר
    """
    if not time_str or time_str == "לא צוין":
        return None
    
    if base_date is None:
        base_date = datetime.now()
    
    # ניקוי המחרוזת
    time_str = time_str.strip()
    
    # חיפוש תאריך - "מחר", "היום", "מחרתיים"
    days_offset = 0
    if "מחר" in time_str:
        days_offset = 1
        time_str = time_str.replace("מחר", "").strip()
    elif "מחרתיים" in time_str:
        days_offset = 2
        time_str = time_str.replace("מחרתיים", "").strip()
    elif "היום" in time_str:
        days_offset = 0
        time_str = time_str.replace("היום", "").strip()
    
    # חיפוש יום בשבוע - "בראשון", "בשני", וכו'
    weekday_map = {
        "ראשון": 6,  # Sunday
        "שני": 0,    # Monday
        "שלישי": 1,  # Tuesday
        "רביעי": 2,  # Wednesday
        "חמישי": 3,  # Thursday
        "שישי": 4,   # Friday
        "שבת": 5,    # Saturday
    }
    
    for day_name, weekday_num in weekday_map.items():
        if day_name in time_str:
            # חישוב יום בשבוע הבא
            current_weekday = base_date.weekday()
            days_until = (weekday_num - current_weekday) % 7
            if days_until == 0:
                days_until = 7  # אם היום הוא היום, קח את השבוע הבא
            days_offset = days_until
            time_str = re.sub(rf"ב?{day_name}\s*", "", time_str).strip()
            break
    
    # חיפוש שעה בפורמט HH:MM או HH:MM:SS
    time_match = re.search(r'(\d{1,2}):(\d{2})(?::(\d{2}))?', time_str)
    if not time_match:
        return None
    
    hour = int(time_match.group(1))
    minute = int(time_match.group(2))
    second = int(time_match.group(3)) if time_match.group(3) else 0
    
    # חיפוש "בוקר", "צהריים", "ערב" לתיקון שעה
    if "בוקר" in time_str or "אחה\"צ" in time_str or "אחר הצהריים" in time_str:
        # אם השעה קטנה מ-12, זה בבוקר/אחר הצהריים
        pass
    elif "ערב" in time_str or "לילה" in time_str:
        # אם השעה קטנה מ-12, זה בערב
        if hour < 12:
            hour += 12
    
    # חישוב התאריך הסופי
    target_date = base_date + timedelta(days=days_offset)
    target_datetime = target_date.replace(hour=hour, minute=minute, second=second, microsecond=0)
    
    return target_datetime


def create_calendar_event(ride: RideSummary, base_date: Optional[datetime] = None) -> Optional[Event]:
    """
    יוצר אירוע לוח שנה מטרמפ.
    
    Args:
        ride: RideSummary עם פרטי הטרמפ
        base_date: תאריך בסיס לחישוב תאריכים
        
    Returns:
        Event object או None אם לא ניתן ליצור אירוע
    """
    # פרסור זמן המפגש
    meeting_datetime = parse_hebrew_time(ride.meeting_time, base_date)
    if not meeting_datetime:
        return None
    
    # יצירת אירוע
    event = Event()
    event.add('summary', f'טרמפ: {ride.driver_name} → {ride.passenger_name}')
    event.add('dtstart', meeting_datetime)
    
    # משך האירוע - שעה אחת (ניתן לשנות)
    event.add('dtend', meeting_datetime + timedelta(hours=1))
    
    # תיאור האירוע
    description_parts = [
        f"נהג: {ride.driver_name}",
        f"נוסע: {ride.passenger_name}",
        f"מיקום איסוף: {ride.pickup_location}",
        f"זמן מפגש: {ride.meeting_time}",
        "",
        f"סיכום: {ride.summary_hebrew}"
    ]
    event.add('description', '\n'.join(description_parts))
    
    # מיקום
    if ride.pickup_location and ride.pickup_location != "לא צוין":
        event.add('location', ride.pickup_location)
    
    # זמן יצירה
    event.add('dtstamp', datetime.now())
    
    # מזהה ייחודי לאירוע
    event.add('uid', f'trempflow-{ride.driver_name}-{ride.passenger_name}-{meeting_datetime.isoformat()}')
    
    return event


def create_calendar_from_rides(rides: List[RideSummary], base_date: Optional[datetime] = None) -> Calendar:
    """
    יוצר לוח שנה (Calendar) מרשימת טרמפים.
    
    Args:
        rides: רשימת RideSummary
        base_date: תאריך בסיס לחישוב תאריכים
        
    Returns:
        Calendar object עם כל האירועים
    """
    cal = Calendar()
    cal.add('prodid', '-//TrempFlow//Calendar//HE')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    cal.add('X-WR-CALNAME', 'טרמפים - TrempFlow')
    cal.add('X-WR-CALDESC', 'אירועי טרמפ שנוצרו מ-TrempFlow')
    cal.add('X-WR-TIMEZONE', 'Asia/Jerusalem')
    
    for ride in rides:
        event = create_calendar_event(ride, base_date)
        if event:
            cal.add_component(event)
    
    return cal


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


def export_batch_to_ical(batch: BatchRideSummary, output_path: str, base_date: Optional[datetime] = None) -> bool:
    """
    מייצא BatchRideSummary לקובץ iCal.
    
    Args:
        batch: BatchRideSummary עם כל הטרמפים
        output_path: נתיב לקובץ הפלט
        base_date: תאריך בסיס לחישוב תאריכים
        
    Returns:
        True אם הצליח, False אחרת
    """
    return export_to_ical(batch.rides, output_path, base_date)
