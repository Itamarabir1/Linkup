"""
סקריפט בדיקה ודמו - מדמה שיחות ומריץ את כל התהליך
"""
import sys
import io

# תיקון encoding ל-Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from analyzer import analyze_ride, analyze_rides_batch
from calendar_integration import export_batch_to_ical, parse_hebrew_time
from schema import RideSummary, BatchRideSummary
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import time


def generate_demo_conversations():
    """
    יוצר רשימה של שיחות מדומות מגוונות לבדיקה
    """
    conversations = [
        # תרחיש 1: שיחה סטנדרטית וברורה עם תאריך ושעה
        """
        יוסי: מישהו נוסע מחר מתל אביב לחיפה?
        אורן: אני יוצא ב-08:00 בבוקר.
        יוסי: מעולה, יכול לאסוף אותי מרכבת מרכז?
        אורן: סגור, נתראה שם.
        """,
        
        # תרחיש 2: שיחה עם יום בשבוע
        """
        דנה: היי, נוסעת לירושלים ביום ראשון?
        מיכל: כן, ב-10:30 בבוקר.
        דנה: מושלם, אני יכולה להצטרף?
        מיכל: בטח, איפה ניפגש?
        דנה: בתחנת הרכבת בירושלים.
        מיכל: סגור, נתראה שם.
        """,
        
        # תרחיש 3: שיחה עם זמן בערב
        """
        רון: מישהו נוסע הערב מתל אביב לבאר שבע?
        שירה: אני יוצאת ב-19:00.
        רון: מעולה, יכול לאסוף אותי מתחנת דרום?
        שירה: כן, בוא.
        """,
        
        # תרחיש 4: שיחה עם כמה אנשים
        """
        תומר: נוסעים מחרתיים מתל אביב לאילת?
        ליאור: אני נוסע ב-06:00 בבוקר.
        נועה: אני גם רוצה להצטרף!
        תומר: מעולה, איפה ניפגש?
        ליאור: בתחנת האוטובוסים המרכזית.
        תומר: סגור.
        נועה: גם אני שם.
        """,
        
        # תרחיש 5: שיחה עם יום שישי
        """
        עמית: יוצאת ביום שישי מתל אביב לחיפה?
        רותם: כן, ב-14:00.
        עמית: מושלם, אני יכול להצטרף?
        רותם: בטח, איפה ניפגש?
        עמית: בתחנת הרכבת מרכז.
        רותם: סגור, נתראה.
        """,
        
        # תרחיש 6: שיחה מבולגנת עם הרבה רעש
        """
        דנה: היי בנות, מה קורה?
        מיכל: הכל טוב! נוסעת אולי לירושלים היום?
        דנה: כן, סביבות 16:00.
        רינת: דנה אל תשכחי להביא את הספר שלי!
        מיכל: דנה, אני יכולה להצטרף? איפה ניפגש?
        דנה: בטח מיכל, בכיכר השעון ביפו.
        """,
        
        # תרחיש 7: טרמפ שלא אושר (מקרה קצה)
        """
        רוני: יוצאת מבאר שבע לאילת בשישי?
        שיר: כן, אבל המכונית מלאה כבר, מצטערת...
        רוני: אופס, אולי פעם אחרת.
        """,
        
        # תרחיש 8: שיחה עם זמן לא מדויק
        """
        ירון: נוסעים היום מתל אביב לאשדוד?
        טל: אני יוצא סביבות 15:30.
        ירון: מעולה, אני יכול להצטרף?
        טל: כן, איפה ניפגש?
        ירון: בתחנת האוטובוסים המרכזית.
        טל: סגור.
        """,
    ]
    
    return conversations


def print_ride_summary(ride: RideSummary, index: int):
    """
    מדפיס סיכום יפה של טרמפ
    """
    print(f"\n{'='*60}")
    print(f"טרמפ #{index + 1}")
    print(f"{'='*60}")
    print(f"👤 נהג: {ride.driver_name}")
    print(f"👤 נוסע: {ride.passenger_name}")
    print(f"📍 מיקום איסוף: {ride.pickup_location}")
    print(f"🕐 זמן מפגש: {ride.meeting_time}")
    print(f"📝 סיכום: {ride.summary_hebrew}")
    
    # בדיקה אם יש זמן תקף
    parsed_time = parse_hebrew_time(ride.meeting_time)
    if parsed_time:
        print(f"✅ זמן מפורש: {parsed_time.strftime('%Y-%m-%d %H:%M')}")
    else:
        print(f"⚠️  לא ניתן לפרסר זמן")


def validate_results(batch: BatchRideSummary):
    """
    בודק שהתוצאות תקינות
    """
    print(f"\n{'='*60}")
    print("🔍 בדיקת תקינות התוצאות")
    print(f"{'='*60}")
    
    total_rides = len(batch.rides)
    valid_rides = 0
    rides_with_time = 0
    rides_with_location = 0
    
    for ride in batch.rides:
        # בדיקה בסיסית
        if ride.driver_name and ride.driver_name != "לא צוין":
            valid_rides += 1
        
        # בדיקת זמן
        if ride.meeting_time and ride.meeting_time != "לא צוין":
            parsed_time = parse_hebrew_time(ride.meeting_time)
            if parsed_time:
                rides_with_time += 1
        
        # בדיקת מיקום
        if ride.pickup_location and ride.pickup_location != "לא צוין":
            rides_with_location += 1
    
    print(f"📊 סטטיסטיקה:")
    print(f"   • סה\"כ טרמפים: {total_rides}")
    print(f"   • טרמפים תקינים: {valid_rides}")
    print(f"   • טרמפים עם זמן תקף: {rides_with_time}")
    print(f"   • טרמפים עם מיקום: {rides_with_location}")
    
    success_rate = (valid_rides / total_rides * 100) if total_rides > 0 else 0
    print(f"\n✅ שיעור הצלחה: {success_rate:.1f}%")
    
    return valid_rides == total_rides


def print_conversation_preview(conversation: str, index: int):
    """
    מדפיס תצוגה מקדימה של שיחה לפני הניתוח
    """
    lines = conversation.strip().split('\n')
    preview_lines = [line.strip() for line in lines if line.strip()][:3]  # 3 שורות ראשונות
    preview = ' | '.join(preview_lines)
    if len(preview) > 70:
        preview = preview[:67] + "..."
    print(f"   [{index + 1}] {preview}")


def analyze_rides_batch_with_progress(conversations: list, max_workers=5):
    """
    מנתח שיחות במקביל עם הצגת progress לכל שיחה בנפרד
    """
    print(f"\n{'='*60}")
    print("📤 שולח שיחות לניתוח במקביל (Parallel Processing)")
    print(f"{'='*60}")
    print(f"⚙️  מספר שיחות: {len(conversations)}")
    print(f"⚙️  מספר threads במקביל: {max_workers}")
    print(f"\n📋 רשימת השיחות שנשלחות:")
    
    # הצגת כל השיחות לפני הניתוח
    for i, conv in enumerate(conversations):
        print_conversation_preview(conv, i)
    
    print(f"\n{'='*60}")
    print("🚀 מתחיל לשלוח שיחות למודל...")
    print(f"{'='*60}\n")
    
    rides = []
    completed = 0
    total = len(conversations)
    start_time = time.time()
    
    # שולח את כל השיחות במקביל
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # שולח את כל המשימות
        future_to_index = {
            executor.submit(analyze_ride, conv, 0.2): i 
            for i, conv in enumerate(conversations)
        }
        
        # אוסף את התוצאות כשהן מגיעות
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            completed += 1
            
            try:
                print(f"⏳ ממתין לשיחה #{index + 1}...", end=" ")
                result_json = future.result()
                
                # ממיר את ה-JSON string חזרה לאובייקט
                result_dict = json.loads(result_json)
                ride_summary = RideSummary(**result_dict)
                rides.append(ride_summary)
                
                elapsed = time.time() - start_time
                print(f"✅ הושלמה! ({completed}/{total}) - {elapsed:.1f} שניות")
                print(f"   👤 נהג: {ride_summary.driver_name} → נוסע: {ride_summary.passenger_name}")
                
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ שגיאה! ({completed}/{total}) - {elapsed:.1f} שניות")
                print(f"   שגיאה: {e}")
                continue
    
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"✨ כל השיחות הושלמו! זמן כולל: {total_time:.1f} שניות")
    print(f"{'='*60}")
    
    return BatchRideSummary(rides=rides)


def main():
    """
    פונקציה ראשית לבדיקה ודמו
    """
    print("="*60)
    print("🧪 סקריפט בדיקה ודמו - TrempFlow")
    print("="*60)
    
    # יצירת שיחות מדומות
    print("\n📝 יוצר שיחות מדומות...")
    demo_conversations = generate_demo_conversations()
    print(f"✅ נוצרו {len(demo_conversations)} שיחות מדומות")
    
    try:
        # ניתוח השיחות עם progress
        batch_result = analyze_rides_batch_with_progress(demo_conversations, max_workers=5)
        
        # הצגת תוצאות מפורטות
        print("\n" + "="*60)
        print("📋 תוצאות הניתוח - כל שיחה בנפרד")
        print("="*60)
        
        for i, ride in enumerate(batch_result.rides):
            print_ride_summary(ride, i)
        
        # בדיקת תקינות
        is_valid = validate_results(batch_result)
        
        # יצירת קובץ לוח שנה
        print("\n" + "="*60)
        print("📅 יצירת קובץ לוח שנה")
        print("="*60)
        
        output_path = "trempflow_demo_calendar.ics"
        base_date = datetime.now()
        
        success = export_batch_to_ical(batch_result, output_path, base_date)
        
        if success:
            abs_path = os.path.abspath(output_path)
            print(f"\n✅ קובץ לוח שנה נוצר בהצלחה!")
            print(f"📁 נתיב: {abs_path}")
            print(f"\n💡 ניתן לייבא את הקובץ ל:")
            print(f"   • Google Calendar")
            print(f"   • Outlook")
            print(f"   • Apple Calendar")
            print(f"   • כל יישום לוח שנה אחר")
        else:
            print("\n❌ שגיאה ביצירת קובץ לוח שנה")
        
        # שמירת תוצאות JSON
        json_output_path = "trempflow_demo_results.json"
        with open(json_output_path, 'w', encoding='utf-8') as f:
            f.write(batch_result.model_dump_json(indent=2, ensure_ascii=False))
        
        print(f"\n💾 תוצאות JSON נשמרו ב: {os.path.abspath(json_output_path)}")
        
        # הסבר על הלוגיקה
        print("\n" + "="*60)
        print("💡 הסבר על הלוגיקה")
        print("="*60)
        print("""
📌 איך זה עובד:
   1. כל שיחה נשלחת בנפרד ל-API של המודל
   2. השיחות נשלחות במקביל (parallel) באמצעות ThreadPoolExecutor
   3. כל שיחה מנותחת באופן עצמאי ומחזירה RideSummary משלה
   4. התוצאות נאספות יחד ל-BatchRideSummary
   5. כל האירועים מתאחדים לקובץ לוח שנה אחד (.ics)

⚡ יתרונות עיבוד במקביל:
   • מהיר יותר - כמה שיחות מעובדות בו-זמנית
   • יעיל יותר - מנצל את זמן ההמתנה ל-API
   • כל שיחה עצמאית - שגיאה באחת לא משפיעה על האחרות
        """)
        
        # סיכום סופי
        print("\n" + "="*60)
        print("✨ בדיקה הושלמה בהצלחה!")
        print("="*60)
        
        if is_valid:
            print("✅ כל הטרמפים נותחו בהצלחה")
        else:
            print("⚠️  חלק מהטרמפים לא נותחו במלואם")
        
    except Exception as e:
        print(f"\n❌ שגיאה במהלך הבדיקה: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
