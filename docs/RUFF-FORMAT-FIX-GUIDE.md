# תיקון קבוע ל־Format check (ruff) ב-CI — מדריך יישום

## דגשים ליישום בטוח

### שלב 1: התיקון — להריץ `ruff format` (לא לתקן ידנית)

- **הכי בטוח:** להריץ `ruff format` על הקובץ. תיקון ידני עלול להשאיר רווח כפול בסוף שורה או שורה ריקה מיותרת ש-Ruff מתעקש עליה.
- **טיפ אחרי ההרצה:** לעוף מבט בקובץ ולוודא ש-ruff לא מחק/שינה משהו שאתה צריך — למשל סדר imports שונה ממה שהתרגלת.

```bash
cd backend
ruff format app/api/v1/routers/passengers.py
# עיין בקובץ ואז:
ruff format --check app/
```

---

### שלב 2: גרסת Ruff — לוודא שה-venv מריץ את הגרסה מ-requirements

- `requirements.txt` עם `ruff==0.15.5` מעולה, אבל צריך לוודא שה-venv **באמת** מריץ את הגרסה הזו.

```bash
cd backend
pip install -r requirements.txt   # ליתר ביטחון
ruff --version                     # צריך להציג 0.15.5
```

---

### שלב 3: Commit ו-Push

- אחרי שהקובץ מפורמט ונקי ועברת עליו בעין:

```bash
git add backend/app/api/v1/routers/passengers.py
git commit -m "fix: apply ruff format to passengers.py, remove debug content"
ruff format --check app/   # אופציונלי — לוודא שכל app/ עובר
git push
```

---

### שלב 4: מניעה — Pre-commit hook (מומלץ בחום)

- Pre-commit hook חוסך את "שכחתי להריץ format" לפני push — הוא מריץ אוטומטית לפני כל commit.
- אפשר להגדיר עם [pre-commit](https://pre-commit.com): הוספת `.pre-commit-config.yaml` והרצת `pre-commit install`, עם hook שרץ `ruff format` על קבצי backend.

---

## סיכום

| שלב | פעולה |
|-----|--------|
| 1 | `ruff format app/api/v1/routers/passengers.py` — לא לתקן ידנית; אחרי כן לעיין בקובץ. |
| 2 | `pip install -r requirements.txt` ו-`ruff --version` — לוודא שה-venv על 0.15.5. |
| 3 | commit + `ruff format --check app/` (אופציונלי) + push. |
| 4 | להמליץ בחום על pre-commit hook כדי לא לשכוח format לפני push. |
