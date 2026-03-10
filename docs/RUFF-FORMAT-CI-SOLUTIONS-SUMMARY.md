# סיכום כל הפתרונות לבעיית "Format check (ruff)" ב-CI

השגיאה: ב-GitHub Actions שלב "Format check (ruff)" נכשל עם `Would reformat: app/api/v1/routers/passengers.py`.

להלן כל האופציות שיושמו או הוזכרו, במצב הנוכחי של הפרויקט. אפשר להשאיר את כולן (המצב כרגע) או לבחור לפי הצורך.

---

## 1. קובץ `.gitattributes` (בשורש הפרויקט)

**מה עושה:** מגדיר שקבצי `*.py` יישמרו ב-Git עם סיום שורה **LF** (ולא CRLF של Windows). כך ב-checkout ב-Linux (CI) וב-Windows מקבלים אותו פורמט.

**תוכן נוכחי:**
```
*.py text eol=lf
```

**נתיב:** [.gitattributes](.gitattributes)

**סטטוס:** פעיל בפרויקט.

---

## 2. שלב "Normalize line endings" ב-workflow

**מה עושה:** ב-CI, לפני הרצת ruff, מריץ פקודה שמסירה `\r` (CR) מכל קבצי `.py` בתיקיית `app/`. כך גם אם איכשהו נשמרו קבצים עם CRLF, ב-CI הם הופכים ל-LF לפני הבדיקה.

**קוד שנוסף ל-** [.github/workflows/backend-ci.yml](.github/workflows/backend-ci.yml)**:**
```yaml
      # זה השלב שפותר את הבעיה - הוא "מנקה" את הקבצים בשרת לפני הבדיקה
      - name: Normalize line endings
        run: find app/ -type f -name "*.py" -exec sed -i 's/\r$//' {} +
```

**מיקום:** אחרי "Install dependencies" ולפני "Lint (ruff)".

**סטטוס:** פעיל בפרויקט.

---

## 3. שינוי אופן בדיקת הפורמט ב-workflow (format + git diff)

**מה עושה:** במקום `ruff format --check app/` (שיכול להיכשל בגלל הבדלים עדינים), מריצים ב-CI את `ruff format app/` ואז `git diff --exit-code`. אם אחרי ה-format יש הבדל מהקוד שנדחף — השלב נכשל. כך הבדיקה מבוססת על השוואת קבצים ולא על לוגיקה פנימית של `--check`.

**קוד נוכחי ב-** [.github/workflows/backend-ci.yml](.github/workflows/backend-ci.yml)**:**
```yaml
      - name: Format check (ruff)
        run: |
          ruff format app/
          git diff --exit-code
```

**סטטוס:** פעיל בפרויקט (זה המצב אחרי "הפתרון הסופי").

---

## 4. צימוד גרסת Ruff (requirements.txt)

**מה עושה:** ב-[backend/requirements.txt](backend/requirements.txt) הוגדר `ruff==0.15.5` כדי שב-CI ובמחשב המקומי תרוץ **אותה גרסה**. גרסאות שונות של ruff יכולות לייצר פורמט שונה ולהוביל ל-"Would reformat" ב-CI.

**שורה ב-requirements.txt:**
```
ruff==0.15.5
```

**במחשב המקומי:** להריץ `pip install -r requirements.txt` (מתוך `backend/`) ולוודא עם `ruff --version` שמתקבל 0.15.5.

**סטטוס:** פעיל בפרויקט.

---

## 5. הגדרה מקומית ב-Git (אופציונלי – "input")

**מה עושה:** אם רוצים ש-Git ימיר ל-LF רק בעת commit (ולא ימיר ל-CRLF ב-checkout ב-Windows), אפשר להגדיר:

```bash
git config core.autocrlf input
```

- **input** = ב-checkout לא לגעת בשורות; ב-commit להמיר CRLF ל-LF.
- משלים ל-.gitattributes: .gitattributes קובע לקבצי `.py`, ו-`core.autocrlf input` הוא כלל גלובלי/מקומי לריפו.

**סטטוס:** לא הוגדר במסגרת השיחה; אופציונלי. אם .gitattributes ו-normalize ב-CI עובדים – לא חובה.

---

## 6. ניקוי הקובץ `passengers.py` והרצת ruff מקומית

**מה עושה:** להסיר מתוך [backend/app/api/v1/routers/passengers.py](backend/app/api/v1/routers/passengers.py) תוכן דיבאג (למשל `# hello world`, `print("...")`) וריווח כפול בין imports, ואז להריץ מקומית:

```bash
cd backend
ruff format app/
```

ואז לעשות commit ו-push. כך הקוד ב-repo זהה ל-output של ruff.

**סטטוס:** בוצע בעבר; הקובץ כרגע נקי. בכל שינוי עתידי בקובץ – להריץ `ruff format app/` לפני commit.

---

## 7. בדיקה מקומית לפני push (כמו ב-CI)

**מה עושה:** להריץ את אותה בדיקה ש-CI מריץ, כדי לראות אם השלב "Format check (ruff)" יעבור:

```powershell
cd c:\Users\user\Desktop\Linkup\backend
ruff format app/
cd ..
git diff --exit-code backend/
```

- אם `git diff --exit-code` מסתיים ב-**0** – הבדיקה עברה.
- אם **1** – יש הבדל; להריץ `git diff backend/` כדי לראות מה לשנות, לעשות commit ו-push.

**סטטוס:** אופציונלי; שימושי לפני כל push ל-backend.

---

## טבלת סיכום – מה פעיל כרגע

| # | פתרון | קובץ/מקום | פעיל? |
|---|--------|-----------|--------|
| 1 | .gitattributes – LF ל-*.py | `.gitattributes` | כן |
| 2 | Normalize line endings ב-CI | `.github/workflows/backend-ci.yml` | כן |
| 3 | Format check = ruff format + git diff | `.github/workflows/backend-ci.yml` | כן |
| 4 | צימוד גרסה ruff==0.15.5 | `backend/requirements.txt` | כן |
| 5 | core.autocrlf input (מקומי) | טרמינל / git config | לא הוגדר |
| 6 | ניקוי passengers.py + ruff format | קובץ + טרמינל | בוצע; לשמור על הרגל |
| 7 | בדיקה מקומית לפני push | טרמינל | אופציונלי |

---

## מה לא לשנות

- **לוגיקה קיימת:** לא לשנות את סדר השלבים ב-workflow או את תוכן הקבצים מלבד אם אתה מתכוון במפורש להסיר/להחליף אחד מהפתרונות למעלה.
- **קבצים:** [.gitattributes](.gitattributes) ו-[.github/workflows/backend-ci.yml](.github/workflows/backend-ci.yml) – כל שינוי בהם משפיע על כל ה-pushים; עדכן רק אם אתה בוחר להסיר או לשנות אחד מהפתרונות.

אם תרצה להסיר פתרון מסוים (למשל את שלב Normalize line endings או לחזור ל-`ruff format --check`), אפשר לעדכן רק את השלב הרלוונטי ב-workflow או את .gitattributes, בלי לשבור את שאר ההגדרות.
