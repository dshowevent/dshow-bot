# D-SHOW WhatsApp Bot 🎉

סוכן מכירות אוטומטי לווצאפ — D-SHOW אטרקציות לאירועים

---

## פריסה ב-Render.com (חינם — 5 דקות)

### שלב 1 — העלה ל-GitHub

1. כנס ל-github.com → New repository → שם: `dshow-bot`
2. העלה את כל הקבצים בתיקיה הזו

### שלב 2 — צור שרת ב-Render

1. כנס ל-render.com → New → Web Service
2. חבר את ה-GitHub repo
3. הגדרות:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn bot:app --workers 1 --threads 2 --timeout 120`
   - **Plan:** Free

### שלב 3 — הכנס את ה-API Keys

ב-Render → Environment Variables:

| Key | Value |
|-----|-------|
| ANTHROPIC_API_KEY | המפתח מהקובץ אתרים.txt |
| GREEN_API_INSTANCE | 7107581380 |
| GREEN_API_TOKEN | הטוקן מהקובץ אתרים.txt |

### שלב 4 — חבר ל-Green API

1. כנס ל-green-api.com → המופע שלך → Notifications
2. הכנס את כתובת ה-Webhook שקיבלת מ-Render:
   `https://dshow-bot.onrender.com/webhook`
3. סמן: ✅ incomingMessageReceived

### שלב 5 — בדיקה

שלח הודעת ווצאפ למספר שלך: "היי אשמח לשמוע על האטרקציות שלכם"
הבוט אמור לענות תוך 10 שניות 🎉

---

## מבנה הקבצים

```
dshow-bot/
├── bot.py          # הבוט המלא
├── requirements.txt
├── render.yaml
└── README.md
```

## תכונות

- ✅ שיחה טבעית בעברית
- ✅ זיכרון שיחה לכל לקוח (30 הודעות אחרונות)
- ✅ בדיקת שעות פעילות (08:00–22:00)
- ✅ כל הסקריפט: פתיחה, תמחור, התנגדויות, סגירה
- ✅ שליחת קישור חוזה Jotform אוטומטי
- ✅ Follow-up sequence
