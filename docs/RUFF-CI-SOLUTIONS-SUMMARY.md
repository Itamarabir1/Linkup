# סיכום כל הפתרונות שניסינו לשגיאת "Format check (ruff)" ב-CI

השגיאה: ב-GitHub Actions שלב "Format check (ruff)" נכשל עם "Would reformat: app/api/v1/routers/passengers.py".

להלן כל האופציות ש**כבר מיושמות** אצלך או ש**ניסינו** — במסמך אחד כדי שתוכלי לבחור מה רלוונטי.

---

## 1. קובץ `.gitattributes` (בשורש הפרויקט)

**מה עשינו:**  
יצרנו קובץ `.gitattributes` עם השורה:
```
*.py text eol=lf
```

**מה זה עושה:**  
מגדיר ל-Git שכל קבצי ה-Python יישמרו ב-repository עם סיום שורה **LF** (Linux/Mac), גם כשעובדים על Windows (שבדרך כלל משתמש ב-CRLF). כך ב-checkout ב-CI (Linux) הקבצים מגיעים עם LF ועקביים.

**איפה:** שורש הפרויקט — `Linkup/.gitattributes`

**סטטוס אצלך:** קיים ופעיל.

---

## 2. שלב "Normalize line endings" ב-workflow

**מה עשינו:**  
הוספנו שלב ב-`.github/workflows/backend-ci.yml` **לפני** "Format check (ruff)":

```yaml
      - name: Normalize line endings
        run: find app/ -type f -name "*.py" -exec sed -i 's/\r$//' {} +
```

**מה זה עושה:**  
ב-CI (Linux), לפני בדיקת הפורמט, מריצים על כל קבצי ה-`.py` בתיקיית `app/` את הפקודה `sed` שמסירה תווי `\r` (CR). כך גם אם איכשהו קבצים עם CRLF הגיעו ל-repo, ב-CI הם הופכים ל-LF לפני ש-ruff רץ.

**איפה:** `.github/workflows/backend-ci.yml` — שלב נפרד בין "Install dependencies" ל-"Lint (ruff)".

**סטטוס אצלך:** קיים ופעיל.

---

## 3. שינוי אופן בדיקת הפורמט ב-workflow (format + git diff)

**מה עשינו:**  
החלפנו את השלב "Format check (ruff)" מ:
```yaml
run: ruff format --check app/
```
ל:
```yaml
      - name: Format check (ruff)
        run: |
          ruff format app/
          git diff --exit-code
```

**מה זה עושה:**  
- במקום רק "לבדוק" עם `--check`, מריצים בפועל `ruff format app/` על הקבצים ב-CI.  
- אחר כך `git diff --exit-code`: אם יש הבדל בין מה ש-checkout הביא לבין מה ש-ruff יצר — השלב נכשל (exit code 1).  
- כך הבדיקה היא "האם הקוד ב-repo **זהה** ל-output של ruff" (כולל ריווח, newlines, line endings), בלי תלות בהתנהגות פנימית של `--check`.

**איפה:** `.github/workflows/backend-ci.yml` — בתוך השלב "Format check (ruff)".

**סטטוס אצלך:** קיים ופעיל.

---

## 4. צימוד גרסת Ruff (requirements.txt)

**מה עשינו:**  
ב-`backend/requirements.txt` צמצמנו את גרסת ruff לגרסה מדויקת:
```
ruff==0.15.5
```
(במקום למשל `ruff>=0.15.0,<0.16` או `ruff>=0.1.0`).

**מה זה עושה:**  
גורם ל-CI (ולסביבה המקומית כשרצים `pip install -r requirements.txt`) להשתמש **בדיוק** באותה גרסת ruff. מונע הבדלי התנהגות בין גרסאות (למשל בין 0.14 ל-0.15) שיכולים לגרום ל-"Would reformat" רק ב-CI.

**איפה:** `backend/requirements.txt` — שורת ה-ruff.

**סטטוס אצלך:** קיים ופעיל.

---

## 5. הרצה מקומית לפני push (טרמינל)

**מה עשינו:**  
הרצנו מקומית (מתוך `backend/`) את אותן פקודות ש-CI מריץ לבדיקת פורמט:
```bash
cd backend
ruff format app/
git diff --exit-code
```

**מה זה עושה:**  
- `ruff format app/` — מתקן פורמט לפי ruff.  
- `git diff --exit-code` — אם יש שינויים (כולל ריווח/שורות), יוצא עם קוד 1.  
אם יוצא 0 — הבדיקה "עברה" מקומית, וסביר שה-CI יעבור אחרי push.

**איפה:** לא קובץ — פקודות להריץ בטרמינל כשעובדים על backend.

**סטטוס:** אופציה להרצה ידנית לפני כל push (או כשמתקנים שגיאות פורמט).

---

## 6. נרמול line endings ב-Git (פעם אחת)

**מה עשינו:**  
אחרי הוספת `.gitattributes` הרצנו:
```bash
git add .gitattributes
git add --renormalize backend/
git status
# ואז commit + push
```

**מה זה עושה:**  
`git add --renormalize backend/` גורם ל-Git לחשב מחדש את ה-blobs של הקבצים ב-`backend/` לפי כללי `.gitattributes`. קבצים שנשמרו בעבר עם CRLF יכולים להישמר מעתה עם LF ב-repo.

**איפה:** לא קובץ — פקודות להרצה פעם אחת אחרי הוספת `.gitattributes`.

**סטטוס:** בוצע בעבר; לא חייבים לחזור על זה אלא אם שינית את `.gitattributes` או הוספת קבצים ישנים מחדש.

---

## 7. תיקון תוכן הקובץ `passengers.py`

**מה עשינו:**  
- הסרנו תוכן דיבאג (למשל `# hello world`, `print("hello world ...")`).  
- תיקנו התנגשות שמות (`status` → `request_status` / `filter_status`).  
- סידרנו imports והסרנו שורות ריקות כפולות.  
- הרצנו `ruff format app/api/v1/routers/passengers.py` ושמרנו את התוצאה.

**מה זה עושה:**  
מבטיח שהקובץ עצמו עומד בכללי ruff ואין בו דברים ש-ruff היה "מתקן" (ולכן גרם ל-"Would reformat").

**איפה:** `backend/app/api/v1/routers/passengers.py`.

**סטטוס:** הקובץ הנוכחי אמור להיות מפורמט ונקי; אם מוסיפים שוב דיבאג או משנים ידנית — להריץ שוב `ruff format app/` ולעשות commit.

---

## 8. טריגר הרצת CI (commit ריק)

**מה עשינו:**  
כדי לראות שההרצה החדשה (עם השלב המעודכן) רצה ב-GitHub:
```bash
git commit --allow-empty -m "ci: trigger Backend CI"
git push
```

**מה זה עושה:**  
יוצר commit ללא שינוי קוד ומפעיל שוב את ה-workflow. שימושי כשמשנים רק את ה-workflow ורוצים לוודא ש-CI רץ על הגרסה המעודכנת.

**סטטוס:** אופציה להרצה ידנית כשצריך "להפעיל" CI מחדש.

---

## טבלת סיכום — מה קיים אצלך עכשיו

| # | פתרון | קובץ/מקום | פעיל אצלך |
|---|--------|-----------|------------|
| 1 | `.gitattributes` — LF ל-*.py | שורש הפרויקט | כן |
| 2 | שלב Normalize line endings (sed) | backend-ci.yml | כן |
| 3 | Format check = ruff format + git diff | backend-ci.yml | כן |
| 4 | גרסת ruff קבועה (ruff==0.15.5) | requirements.txt | כן |
| 5 | הרצה מקומית לפני push | טרמינל | לבחירתך |
| 6 | נרמול (--renormalize) | טרמינל, פעם אחת | בוצע בעבר |
| 7 | ניקוי passengers.py + ruff format | passengers.py | כן |
| 8 | commit ריק לטריגר CI | טרמינל | לבחירתך |

---

## מה לא לשנות

- **אל תחזירי** את השלב ל-`ruff format --check app/` לבד — הפתרון שעובד אצלך הוא `ruff format app/` + `git diff --exit-code`.
- **אל תמחקי** את שלב "Normalize line endings" — הוא עוזר במקרה שיש CRLF ב-repo.
- **אל תמחקי** את `.gitattributes` — הוא מוודא ש-*.py נשמרים עם LF.

אם תרצי לכבות אופציה מסוימת (למשל את שלב הנרמול) — אפשר לעשות זאת בהדרגה ולבדוק ב-CI אחרי כל שינוי.
