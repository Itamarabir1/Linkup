# מה זה CI/CD ומה הקבצים שנוספו לפרויקט

## מה זה CI/CD בקצרה?

**CI** = Continuous Integration (אינטגרציה רציפה)  
**CD** = Continuous Delivery/Deployment (משלוח/פריסה רציפה)

בפשטות:
- **CI** = כל פעם שמישהו דוחף קוד ל-GitHub (או פותח Pull Request), רץ אוטומטית "בודק איכות": האם הקוד עובר lint, האם הטסטים עוברים, האם הבילד עובר. אם משהו נכשל – רואים את זה מיד ב-GitHub, בלי להריץ הכל ידנית במחשב.
- **CD** = אחרי שה-CI עבר, אפשר אוטומטית לפרוס (להעלות) את האפליקציה לשרת (למשל Render, Vercel וכו').

בפרויקט שלך כרגע יש **רק CI** – בדיקות אוטומטיות ב-GitHub. אין עדיין פריסה אוטומטית (CD) מלאה, אבל יש קובץ הגדרות לשרת (render.yaml).

---

## רשימת הקבצים שנוספו / קשורים ל-CI-CD וסביבת פיתוח

### 1. קבצי ה-CI עצמו (GitHub Actions)

| קובץ | מה הוא עושה |
|------|--------------|
| **`.github/workflows/backend-ci.yml`** | כל push/PR שמשנה משהו ב-`backend/`: מתקין Python 3.11, מתקין תלויות, מריץ **ruff check** (lint), **ruff format --check** (בדיקת פורמט), ו-**pytest** (טסטים). אם משהו נכשל – ה-workflow נכשל. |
| **`.github/workflows/frontend-ci.yml`** | אותו רעיון ל-`frontend/`: Node 20, `npm ci`, **npm run lint**, **npm run build**. בודק שהפרונט עובר lint ובנייה. |
| **`.github/workflows/chat-ws-ci.yml`** | אותו רעיון ל-`chat-ws/` (Go): Go 1.21, **go mod download**, **go build**, **go vet**. בודק שה-chat service נבנה ועובר vet. |

אלה **שלושת הקבצים המרכזיים** של ה-CI: הם מגדירים "מה לרוץ ובאיזה סדר" בכל push/PR.

---

### 2. קבצי הגדרה שקשורים ל-CI ולכלים

| קובץ | מה הוא עושה |
|------|--------------|
| **`.gitattributes`** | מגדיר ש-**קבצי Python** (`.py`) יישמרו ב-Git עם סיום שורה **LF** (לא CRLF). זה מונע מצב שבו אצלך הקוד "מפורמט" ובמחשב של ה-CI (Linux) ruff חושב שצריך לפרמט מחדש – כי ההבדל היה רק line endings. |
| **`backend/requirements.txt`** (השורה של ruff) | נוספה שורה **ruff** כדי שב-CI יהיה מותקן אותו כלי שמריץ `ruff check` ו-`ruff format --check`. בלי זה ב-GitHub Actions היה יוצא "ruff: command not found". |
| **`backend/pyrightconfig.json`** | לא רץ ב-CI, אלא **ב-VSCode/Cursor**: אומר ל-Pylance/Pyright איפה ה-venv ואיזו גרסת Python. עוזר לך locally עם השלמות וסימון שגיאות. |

---

### 3. קבצים לסביבת העריכה (VSCode/Cursor)

| קובץ | מה הוא עושה |
|------|--------------|
| **`.vscode/settings.json`** | הגדרות לפרויקט: איזה Python interpreter להשתמש (backend/.venv), איפה לחפש מודולים (extraPaths), ואיזה formatter ברירת מחדל ל-Python. משפיע רק עליך בעורך, לא על ה-CI. |

---

### 4. קבצים שקשורים ל-deploy (פריסה) – לא רץ אוטומטית ב-CI

| קובץ | מה הוא עושה |
|------|--------------|
| **`render.yaml`** (אם קיים בשורש הפרויקט) | קובץ הגדרות ל-**Render** (שירות אירוח). מתאר אילו שירותים להריץ (backend, frontend וכו') ואיך לבנות אותם. משמש כשמעלים ידנית ל-Render או כשמחברים GitHub ל-Render לפריסה אוטומטית. |

---

### 5. קבצים שנוצרים אוטומטית (לא צריך לערוך)

| קובץ/תיקייה | מה זה |
|--------------|--------|
| **`backend/.ruff_cache/`** | קאש של **ruff**. אחרי שרצים `ruff check` או `ruff format` נוצרת התיקייה הזו. בדרך כלל מוסיפים ל-.gitignore כדי שלא ייכנס ל-Git. |
| **`backend/.venv/`** | הסביבה הווירטואלית של Python אצלך במחשב. לא נדחף ל-Git (מופיע ב-.gitignore). ה-CI יוצר venv משלו בכל הרצה. |

---

## סיכום זרימה – "מה קורה כשאני עושה push?"

1. אתה עושה **git push** ל-`main` או `develop`.
2. GitHub מפעיל לפי **paths**:
   - שינית משהו ב-**backend/** → רץ **backend-ci.yml** (Python, ruff, pytest).
   - שינית משהו ב-**frontend/** → רץ **frontend-ci.yml** (Node, lint, build).
   - שינית משהו ב-**chat-ws/** → רץ **chat-ws-ci.yml** (Go, build, vet).
3. אם כל ה-steps ב-workflow שעורר עוברים – ה-CI מסומן בירוק. אם step נכשל (למשל `ruff format --check` או `pytest`) – ה-CI אדום ורואים ב-GitHub איפה נכשל.
4. **אין** עדיין שלב אוטומטי שמריץ "עכשיו תעלה את האתר לשרת" – את זה עושים ידנית או דרך חיבור GitHub ל-Render/שירות אירוח.

---

## טבלה מהירה – "הקובץ הזה בשביל מה?"

| קובץ | בשביל CI (ב-GitHub) | בשביל העורך (אצלך) | בשביל פריסה |
|------|----------------------|---------------------|---------------|
| `.github/workflows/*.yml` | ✅ רץ אוטומטית | ❌ | ❌ |
| `.gitattributes` | ✅ משפיע על איך הקבצים נשמרים ב-Git | ❌ | ❌ |
| `backend/requirements.txt` (ruff) | ✅ מותקן ב-CI | ✅ אם תריץ ruff מקומית | ❌ |
| `backend/pyrightconfig.json` | ❌ | ✅ Pylance/Pyright | ❌ |
| `.vscode/settings.json` | ❌ | ✅ interpreter ו-formatter | ❌ |
| `render.yaml` | ❌ | ❌ | ✅ הגדרות שרת |
