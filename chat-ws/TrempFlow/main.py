from analyzer import analyze_rides_batch
from mock_data import MOCK_CONVERSATIONS
from calendar_integration import export_batch_to_ical
from datetime import datetime
import os


def main():
    """פונקציה ראשית של האפליקציה"""
    print("🚗 מנתח שיחות טרמפ - TrempFlow\n")
    
    # ניתוח השיחות
    batch_result = analyze_rides_batch(MOCK_CONVERSATIONS)
    print(batch_result.model_dump_json(indent=2, ensure_ascii=False))
    
    # יצירת קובץ לוח שנה
    print("\n📅 יוצר קובץ לוח שנה...")
    output_path = "trempflow_calendar.ics"
    base_date = datetime.now()  # תאריך בסיס לחישוב תאריכים
    
    success = export_batch_to_ical(batch_result, output_path, base_date)
    
    if success:
        abs_path = os.path.abspath(output_path)
        print(f"✅ קובץ לוח שנה נוצר בהצלחה: {abs_path}")
        print(f"💡 ניתן לייבא את הקובץ ל-Google Calendar, Outlook, Apple Calendar וכו'")
    else:
        print("❌ שגיאה ביצירת קובץ לוח שנה")


if __name__ == "__main__":
    main()
