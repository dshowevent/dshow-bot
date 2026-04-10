"""
D-SHOW WhatsApp Sales Bot
סוכן מכירות אוטומטי לווצאפ — D-SHOW אטרקציות לאירועים
"""

import os
import json
import re
from datetime import datetime, time
import pytz
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ─────────────────────────────────────────
# הגדרות
# ─────────────────────────────────────────
ANTHROPIC_API_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")
GREEN_API_INSTANCE  = os.environ.get("GREEN_API_INSTANCE", "7107581380")
GREEN_API_TOKEN     = os.environ.get("GREEN_API_TOKEN", "")
GOOGLE_CREDS_JSON   = os.environ.get("GOOGLE_CREDS_JSON", "")   # JSON של service account
SHEET_NAME          = "D-SHOW Bot Memory"
ISRAEL_TZ           = pytz.timezone("Asia/Jerusalem")
BOT_START_HOUR      = 8
BOT_END_HOUR        = 22

# ─────────────────────────────────────────
# System Prompt — סוכן D-SHOW
# ─────────────────────────────────────────
SYSTEM_PROMPT = """
## זהות ותפקיד

אתה סוכן מכירות של D-SHOW — חברה לאטרקציות לאירועים ברמלה עם ניסיון של 10+ שנים ואלפי אירועים. אתה מגיב בווצאפ ללקוחות פוטנציאליים.

המטרה שלך: לאסוף פרטי אירוע, להציע חבילה מתאימה, לטפל בהתנגדויות, ולסגור עסקה — הכל תוך שמירה על סגנון חם, אנושי ונינוח. לא בוטי.

## כללי סגנון — חובה

- כתוב כמו בן אדם אמיתי בווצאפ — קצר, ישיר, חם
- אסור: מקפים ארוכים (—), רשימות ארוכות, ניסוח פורמלי
- מותר: אמוג'ים (במידה), משפטים קצרים, שפה דבורה
- אל תחשוף שאתה AI — אם שואלים "אני מהצוות של D-SHOW 😊"
- תמיד לתת מחיר סופי בלבד — ללא פירוט תוספות נסיעה / אחוזים

## שלב 1 — פתיחה וזיהוי

כשלקוח פונה לראשונה — שאל 4 שאלות בהודעה אחת:

"היי! שמחים שפנית 😊
ספר לי קצת על האירוע:
🎊 מה סוג האירוע?
📍 באיזה עיר?
🗓️ מה התאריך?
👥 כמה אורחים בערך?"

אם מבקש מחיר לפני פרטים: "המחיר תלוי במיקום ובכמות האורחים — ספר לי רק שני דברים: באיזה עיר וכמה אורחים? ואני נותן לך מחיר מיידית 😊"

## שלב 2 — בדיקת מיקום ותאריך

מיקום:
- גדרה עד חדרה → המשך רגיל, ללא תוספת
- מחוץ לגדרה/חדרה עד באר שבע/קיסריה → גלם 200 ₪ במחיר הסופי, אל תזכיר ללקוח
- מחוץ לתחום (מעבר לקיסריה/באר שבע, אילת, דימונה, כפרים ערבים) → "לצערי האזור הזה מחוץ לאזור הפעילות שלנו 🙏 אם יהיה לכם אירוע במרכז נשמח לעזור!"

תאריך:
- שבת / חג יהודי (ראש השנה, יום כיפור, סוכות ראשון+שמיני עצרת, פסח ראשון+אחרון, שבועות) → "התאריך הזה לא זמין עבורנו, אנחנו שומרי שבת 🙏 יש לכם תאריך חלופי?"
- יום שישי → ווודא סיום 3 שעות לפני שקיעה (חורף עד 13:30, קיץ עד 16:45)
- תאריך תקין → המשך

## שלב 3 — הצגת חבילה / הצעת מחיר

חבילות:
- ברית → עמדת צילום או מגנטים + קיר בלונים + 4 בלוקי עץ → 1,800–2,000 ₪
- בר/בת מצווה → עמדת 360 + עמדת צילום + 4 שולחנות משחק + קיר צילום → 3,500 ₪
- חתונה → עמדת צילום או מגנטים + זיקוקים + חבילת סלואו + קיאק פירות + קיר משקפיים → 4,500 ₪
- אחר → שאל מה מחפשים, הצע 2–3 אטרקציות

כללי תמחור:
1. לא לתת מחיר לפני מיקום + כמות אורחים
2. לא להזכיר תוספות נסיעה — מחיר סופי בלבד
3. לפתוח תמיד במחיר גבוה מהמינימום
4. קורפורייט = מחיר גבוה יותר מלקוח פרטי
5. פורים ותאריכים מבוקשים = +60% על הכל

תוספת מגנטים לפי אורחים:
- עד 600 → 1,500 ₪ (ללא תוספת)
- 600–1,000 → 1,875 ₪ (+25%)
- 1,000–1,400 → 2,250 ₪ (+50%)
- 1,400+ → 2,625 ₪ (+75%)

עמדות צילום לפי אורחים:
- עד 700 → 1 עמדה → 1,400 ₪ פרטי / 1,700 ₪ חברה
- 700–1,400 → 2 עמדות → 2,800 / 3,400 ₪
- 1,400–2,100 → 3 עמדות → 4,000 / 5,000 ₪
- 2,100+ → 4 עמדות → 5,200 / 6,500 ₪

הורדת אטרקציה מחבילה: לרדת רק 700–800 ₪, לא את מחיר האטרקציה המלא.

## שלב 4 — טיפול בהתנגדויות

"יקר לי" / "תעשה מחיר":
- שאל: "מה התקציב שלך לאטרקציות?"
- הפרש קטן (עד 300 ₪) → ירידה קטנה חד-פעמית
- "יאללה נו" / "תעגל" → "זה כבר המחיר הסופי שלי 😊"

"אני צריך לחשוב":
- "בהחלט 😊" + "אנחנו עמוסים, כדאי לשריין את התאריך"
- הצע שריון: "300 ₪ בלבד לנעילה — השאר ביום האירוע"

"ראיתי אצל אחרים יותר זול": לא להתמודד על מחיר. "10+ שנים, אלפי אירועים — ביום האירוע שלך לא תרצה הפתעות 😊"

"צריך להתייעץ עם בן/בת הזוג": "שולח לך פרטים מסודרים להראות לו/ה 👌" + דחיפות עדינה

"אפשר בתשלומים?": "300 ₪ מקדמה עכשיו, השאר ביום האירוע — בפועל שני שלבים 👌"

"ניסיון רע בעבר": הקשב, "זה בדיוק מה שלא קורה אצלנו — אלפי אירועים, מגיעים עם גיבוי"

"יש ביטוח/רישיון?": "כן, יש לנו הכל — עוסק מורשה מלא 😊"

"מה קורה בגשם?": "כל האטרקציות מתאימות גם לפנים 😊"

לקוח כועס: "אני מעביר אותך לבעלים שיטפל אישית 🙏"

## שלב 5 — סגירה

כשלקוח מסכים:
"מעולה! 🎉
בואו נסדר:
1️⃣ חוזה דיגיטלי עם כל פרטי האירוע
2️⃣ אחרי חתימה — 300 ₪ מקדמה לשריון התאריך
3️⃣ היתרה ביום האירוע — ביט / פייבוקס / מזומן

שולח לחוזה עכשיו 👇
📄 https://form.jotform.com/251117636038453
ממלאים וחותמים — 2 דקות ✍️"

טכניקות סגירה:
- Assumptive: "מה שם מלא לחוזה?" / "מה הכתובת של האולם?"
- Two-Option: "ביט או פייבוקס למקדמה?" / "טאבלט או מצלמה DSLR?"
- Urgency (רק אם אמיתי): "יש פנייה נוספת על התאריך 🙏"
- Value: "זה יוצא פחות מ-X ₪ לאדם 😊"
- Last Push (פעם אחת): "עשיתי את המקסימום. זה המחיר הכי טוב. תחליטו עד [יום/שעה] ✅"

## שלב 6 — אישור סופי (אחרי חתימה)

"האירוע שלכם נרשם! 🎊
📅 תאריך: [תאריך]
📍 מיקום: [עיר/אולם]
🎯 אטרקציות: [רשימה]
💰 סה״כ: [סכום] ₪ | ✅ מקדמה: 300 ₪ | 💳 יתרה: [סכום] ₪ ביום
נשלח תזכורת יום לפני 😊 מחכים! 🙌"

## שלב 7 — Follow-up (לקוח שלא ענה)

24 שעות: "היי! רציתי לוודא שקיבלת את הפרטים 😊 יש שאלות?"
3 ימים: "שלום! התאריך עדיין פנוי 😊 [סיכום] יש שאלות? 🙏"
7 ימים: "היי 😊 מניח שהתקדמתם עם ספק אחר — אין בעיה! אם תצטרכו בעתיד — נשמח 🙏"
אחרי 3 הודעות ללא תגובה — עצור.

## פרטי האטרקציות (לפי בקשה)

עמדת צילום — 1,400 ₪ פרטי, טאבלט/DSLR, הדפסה 30 שניות, שליחה QR/מייל
עמדת 360° — 1,400–1,500 ₪, 4 אנשים, סרטון 20 שניות, 3×3 מטר
מגנטים — 1,500 ₪ (עד 600 איש), 2 אנשי צוות, מגנט 7×10, לוח ברחבה
קיאק פירות — 1,400–1,500 ₪, 3 מטר, ~50 ק"ג פירות, ללא חשמל
קיר משקפיים — 1,300 ₪, 72 זוגות, תוספת 10 ₪ לזוג
שולחנות משחק — 1,200 ₪ ל-4, +300 ₪ כל שולחן נוסף
סלואו — 1,300 ₪ (עם זיקוקים 1,600 ₪), עשן + בלונים/נוצות
זיקוקים קרים — 700 ₪, 6 זיקוקים, לבדוק אישור אולם
בלוקי עץ — 13–18 ₪ ליחידה, מינימום 50
קיר בלונים — 1,200 ₪ פתיחה, מינימום 800 ₪

## מה אסור

- לחשוף שאתה AI
- לתת מחיר לפני מיקום + אורחים
- לפרט תוספות נסיעה
- להמליץ על מתחרים
- לתת הנחה יותר מפעם אחת
- לטפל בתלונות/פיצויים — להעביר לבעלים
""".strip()


# ─────────────────────────────────────────
# Google Sheets — ניהול היסטוריית שיחות
# ─────────────────────────────────────────
import gspread
from google.oauth2.service_account import Credentials

_sheet_cache = None
_sheet_failed = False  # אם נכשל — לא לנסות שוב בכל request

def get_sheet():
    """מחזיר את גיליון ה-conversations, עם cache. יוצר אותו אם לא קיים."""
    global _sheet_cache, _sheet_failed
    if _sheet_cache is not None:
        return _sheet_cache
    if _sheet_failed:
        return None
    if not GOOGLE_CREDS_JSON:
        print("[Sheets Error] GOOGLE_CREDS_JSON env var is empty — running without memory")
        _sheet_failed = True
        return None
    try:
        creds_info = json.loads(GOOGLE_CREDS_JSON)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open(SHEET_NAME)

        # נסה לפתוח את הטאב conversations
        try:
            ws = spreadsheet.worksheet("conversations")
        except gspread.exceptions.WorksheetNotFound:
            print("[Sheets] Worksheet 'conversations' not found — creating it...")
            ws = spreadsheet.add_worksheet(title="conversations", rows=1000, cols=3)
            ws.append_row(["phone_number", "history", "last_updated"])
            print("[Sheets] Worksheet 'conversations' created with headers.")

        # וודא שיש כותרות בשורה 1
        headers = ws.row_values(1)
        if not headers or headers[0] != "phone_number":
            ws.update("A1:C1", [["phone_number", "history", "last_updated"]])
            print("[Sheets] Headers written to row 1.")

        _sheet_cache = ws
        print("[Sheets] Connected successfully ✓")
        return _sheet_cache
    except Exception as e:
        print(f"[Sheets Error] {e}")
        _sheet_failed = True
        return None


def get_conversation(phone: str) -> list:
    sheet = get_sheet()
    if sheet is None:
        return []
    try:
        records = sheet.get_all_records()
        for row in records:
            if str(row.get("phone_number", "")) == phone:
                raw = row.get("history", "[]")
                return json.loads(raw) if raw else []
        return []
    except Exception as e:
        print(f"[Sheets Read Error] {e}")
        return []


def update_conversation(phone: str, role: str, content: str):
    sheet = get_sheet()
    if sheet is None:
        return
    try:
        history = get_conversation(phone)
        history.append({"role": role, "content": content})
        history = history[-30:]  # שמור 30 הודעות אחרונות
        history_json = json.dumps(history, ensure_ascii=False)
        now_str = datetime.now(ISRAEL_TZ).strftime("%Y-%m-%d %H:%M")

        # חפש שורה קיימת לפי מספר טלפון
        records = sheet.get_all_records()
        for i, row in enumerate(records, start=2):  # שורה 1 = כותרות
            if str(row.get("phone_number", "")) == phone:
                sheet.update(f"B{i}", [[history_json]])
                sheet.update(f"C{i}", [[now_str]])
                return

        # לא נמצאה שורה — הוסף חדשה
        sheet.append_row([phone, history_json, now_str])
    except Exception as e:
        print(f"[Sheets Write Error] {e}")


# ─────────────────────────────────────────
# בדיקת שעות פעילות (08:00–22:00 ישראל)
# ─────────────────────────────────────────
def is_active_hours() -> bool:
    now = datetime.now(ISRAEL_TZ).time()
    return time(BOT_START_HOUR, 0) <= now <= time(BOT_END_HOUR, 0)


# ─────────────────────────────────────────
# שליחת הודעת ווצאפ דרך Green API
# ─────────────────────────────────────────
def send_whatsapp(chat_id: str, message: str) -> bool:
    url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
    payload = {"chatId": chat_id, "message": message}
    try:
        r = requests.post(url, json=payload, timeout=15)
        return r.status_code == 200
    except Exception as e:
        print(f"[Green API Error] {e}")
        return False


# ─────────────────────────────────────────
# קריאה ל-Claude API (HTTP ישיר — בלי SDK)
# ─────────────────────────────────────────
def get_claude_response(phone: str, user_message: str) -> str:
    history = get_conversation(phone)
    messages = history + [{"role": "user", "content": user_message}]

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-opus-4-5",
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": messages,
    }
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"]
    except Exception as e:
        print(f"[Claude API Error] {e}")
        return "מצטערים, יש תקלה טכנית זמנית 🙏 נחזור אליכם בהקדם!"


# ─────────────────────────────────────────
# Webhook — הנקודה שGreen API שולח אליה
# ─────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json or {}

    # סנן רק הודעות נכנסות מלקוחות (לא מהבוט עצמו)
    if data.get("typeWebhook") != "incomingMessageReceived":
        return jsonify({"status": "ignored"}), 200

    msg_data = data.get("messageData", {})
    msg_type = msg_data.get("typeMessage", "")

    # רק הודעות טקסט
    if msg_type != "textMessage":
        return jsonify({"status": "ignored"}), 200

    user_message = msg_data.get("textMessageData", {}).get("textMessage", "").strip()
    chat_id      = data.get("senderData", {}).get("sender", "")
    phone        = re.sub(r"@.*", "", chat_id)  # 972XXXXXXXXX

    if not user_message or not chat_id:
        return jsonify({"status": "ignored"}), 200

    print(f"[IN] {phone}: {user_message}")

    # בדיקת שעות פעילות
    if not is_active_hours():
        # שלח הודעה חד-פעמית שעות לא פעילות (בדוק האם כבר נשלחה)
        history = get_conversation(phone)
        last_msgs = [m["content"] for m in history[-3:] if m["role"] == "assistant"]
        if not any("מחוץ לשעות" in m or "08:00" in m for m in last_msgs):
            off_msg = "שלום! שעות הפעילות שלנו הן 08:00–22:00 😊 נחזור אליכם בבוקר!"
            send_whatsapp(chat_id, off_msg)
            update_conversation(phone, "user", user_message)
            update_conversation(phone, "assistant", off_msg)
        return jsonify({"status": "outside_hours"}), 200

    # קבל תגובה מ-Claude
    bot_reply = get_claude_response(phone, user_message)
    print(f"[OUT] {phone}: {bot_reply[:80]}...")

    # שמור בהיסטוריה
    update_conversation(phone, "user", user_message)
    update_conversation(phone, "assistant", bot_reply)

    # שלח חזרה ללקוח
    send_whatsapp(chat_id, bot_reply)

    return jsonify({"status": "sent"}), 200


# ─────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({
        "status": "ok",
        "bot": "D-SHOW WhatsApp Sales Bot",
        "version": "3.0",
        "active_hours": f"{BOT_START_HOUR}:00–{BOT_END_HOUR}:00 Israel"
    })


@app.route("/", methods=["GET"])
def index():
    return "🎉 D-SHOW Bot is running!", 200


# ─────────────────────────────────────────
# ממשק אימון — /train
# ─────────────────────────────────────────
TRAIN_HTML = """<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>D-SHOW | אימון סוכן</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#0D0D0D; color:#F5F3EE; font-family:'Segoe UI',Arial,sans-serif; height:100vh; display:flex; flex-direction:column; }
.header { background:#141414; border-bottom:1px solid #242424; padding:14px 20px; display:flex; align-items:center; gap:12px; }
.header h1 { font-size:16px; font-weight:700; color:#C9A84C; }
.header .badge { font-size:11px; background:rgba(37,211,102,0.15); color:#25D366; padding:3px 10px; border-radius:20px; }
.reset-btn { margin-right:auto; background:rgba(224,85,85,0.15); color:#E05555; border:1px solid rgba(224,85,85,0.3); padding:6px 14px; border-radius:8px; cursor:pointer; font-size:12px; }
.reset-btn:hover { background:rgba(224,85,85,0.25); }
.chat { flex:1; overflow-y:auto; padding:20px; display:flex; flex-direction:column; gap:12px; }
.msg { display:flex; flex-direction:column; max-width:75%; }
.msg.user { align-self:flex-start; }
.msg.bot { align-self:flex-end; }
.msg-label { font-size:11px; color:#6B6B6B; margin-bottom:4px; padding:0 4px; }
.msg.bot .msg-label { text-align:left; }
.bubble { padding:10px 14px; border-radius:12px; font-size:14px; line-height:1.6; white-space:pre-wrap; word-break:break-word; }
.msg.user .bubble { background:#1F3A2A; color:#DCF8C6; border-bottom-right-radius:3px; }
.msg.bot .bubble { background:#242424; color:#F5F3EE; border-bottom-left-radius:3px; }
.typing .bubble { color:#6B6B6B; font-style:italic; }
.input-area { background:#141414; border-top:1px solid #242424; padding:14px 16px; display:flex; gap:10px; align-items:flex-end; }
textarea { flex:1; background:#1C1C1C; border:1px solid #242424; border-radius:10px; color:#F5F3EE; font-size:14px; padding:10px 14px; resize:none; outline:none; font-family:inherit; min-height:44px; max-height:120px; }
textarea:focus { border-color:#C9A84C; }
button#send { background:#C9A84C; color:#0D0D0D; border:none; border-radius:10px; padding:10px 20px; font-weight:700; font-size:14px; cursor:pointer; height:44px; white-space:nowrap; }
button#send:hover { background:#E8C96A; }
button#send:disabled { background:#333; color:#666; cursor:not-allowed; }
.empty-state { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px; color:#6B6B6B; }
.empty-state .icon { font-size:40px; }
</style>
</head>
<body>
<div class="header">
  <span style="font-size:20px">🎯</span>
  <h1>D-SHOW — סימולטור אימון</h1>
  <span class="badge">● סוכן פעיל</span>
  <button class="reset-btn" onclick="resetChat()">🗑 אפס שיחה</button>
</div>
<div class="chat" id="chat">
  <div class="empty-state">
    <div class="icon">💬</div>
    <div>שלח הודעה לתרגל עם הסוכן</div>
    <div style="font-size:12px">דוגמה: "היי אשמח לשמוע על האטרקציות שלכם"</div>
  </div>
</div>
<div class="input-area">
  <textarea id="msg" placeholder="כתוב הודעה כאילו אתה לקוח..." rows="1" onkeydown="handleKey(event)" oninput="autoResize(this)"></textarea>
  <button id="send" onclick="sendMsg()">שלח</button>
</div>
<script>
const SESSION_ID = 'train_' + Math.random().toString(36).substr(2,9);
let chatEl = document.getElementById('chat');
let sending = false;

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); }
}

function addMsg(role, text) {
  let empty = chatEl.querySelector('.empty-state');
  if (empty) empty.remove();
  let div = document.createElement('div');
  div.className = 'msg ' + role;
  div.innerHTML = `<div class="msg-label">${role === 'user' ? '👤 לקוח (אתה)' : '🤖 סוכן D-SHOW'}</div><div class="bubble">${text.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div>`;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
  return div;
}

async function sendMsg() {
  if (sending) return;
  let ta = document.getElementById('msg');
  let text = ta.value.trim();
  if (!text) return;
  ta.value = '';
  ta.style.height = 'auto';
  addMsg('user', text);
  sending = true;
  document.getElementById('send').disabled = true;
  let typingEl = addMsg('bot typing', '...');
  try {
    let res = await fetch('/train/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({session: SESSION_ID, message: text})
    });
    let data = await res.json();
    typingEl.remove();
    addMsg('bot', data.reply || 'שגיאה בקבלת תגובה');
  } catch(e) {
    typingEl.remove();
    addMsg('bot', 'שגיאת חיבור 🙏');
  }
  sending = false;
  document.getElementById('send').disabled = false;
  ta.focus();
}

async function resetChat() {
  await fetch('/train/reset', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({session: SESSION_ID})});
  chatEl.innerHTML = '<div class="empty-state"><div class="icon">💬</div><div>שיחה אופסה — התחל מחדש</div></div>';
}
</script>
</body>
</html>"""


@app.route("/train", methods=["GET"])
def train_page():
    return TRAIN_HTML


@app.route("/train/chat", methods=["POST"])
def train_chat():
    data = request.json or {}
    session_id = data.get("session", "train_default")
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"reply": ""}), 400
    reply = get_claude_response(session_id, user_message)
    update_conversation(session_id, "user", user_message)
    update_conversation(session_id, "assistant", reply)
    return jsonify({"reply": reply})


@app.route("/train/reset", methods=["POST"])
def train_reset():
    data = request.json or {}
    session_id = data.get("session", "train_default")
    # מחק את ה-session מה-Sheets
    sheet = get_sheet()
    if sheet is not None:
        try:
            records = sheet.get_all_records()
            for i, row in enumerate(records, start=2):
                if str(row.get("phone_number", "")) == session_id:
                    sheet.update(f"B{i}", [[json.dumps([], ensure_ascii=False)]])
                    break
        except Exception as e:
            print(f"[Train Reset Error] {e}")
    return jsonify({"status": "reset"})


@app.route("/status", methods=["GET"])
def status():
    """בדיקת סטטוס כל הרכיבים"""
    results = {
        "bot": "D-SHOW WhatsApp Sales Bot v3.0",
        "anthropic_key": "✓ set" if ANTHROPIC_API_KEY else "✗ MISSING",
        "green_api_instance": GREEN_API_INSTANCE or "✗ MISSING",
        "green_api_token": "✓ set" if GREEN_API_TOKEN else "✗ MISSING",
        "google_creds": "✓ set" if GOOGLE_CREDS_JSON else "✗ MISSING",
        "sheets_connection": "unknown",
    }
    # בדוק חיבור לשיטס
    sheet = get_sheet()
    if sheet is not None:
        results["sheets_connection"] = f"✓ connected to '{sheet.title}'"
    else:
        results["sheets_connection"] = "✗ failed (check logs)"
    return jsonify(results)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "bot": "D-SHOW WhatsApp Sales Bot", "version": "3.0"})


# ─────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
