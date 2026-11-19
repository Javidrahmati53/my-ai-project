import ast, json, operator, os, random, re, sqlite3, time
import urllib.parse, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.getenv("BOT_TOKEN", "").strip()
TIMEZONE = os.getenv("TIMEZONE", "Asia/Baku")
DB_FILE = "poneix_data.sqlite3"
if not TOKEN:
    raise SystemExit("Set BOT_TOKEN in GitHub Actions Secrets.")
API = "https://api.telegram.org/bot" + TOKEN + "/"

def db():
    return sqlite3.connect(DB_FILE)

def api(method, params=None):
    request = urllib.request.Request(API + method, data=urllib.parse.urlencode(params or {}).encode())
    with urllib.request.urlopen(request, timeout=45) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError(result.get("description", "Telegram API error"))
    return result["result"]

def send(chat_id, text):
    text = str(text)
    for start in range(0, max(1, len(text)), 4000):
        api("sendMessage", {"chat_id": chat_id, "text": text[start:start + 4000] or " "})

def init_db():
    with db() as con:
        con.execute("CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY, chat INTEGER, body TEXT)")
        con.execute("CREATE TABLE IF NOT EXISTS todos(id INTEGER PRIMARY KEY, chat INTEGER, body TEXT, done INTEGER DEFAULT 0)")
        con.execute("CREATE TABLE IF NOT EXISTS reminders(id INTEGER PRIMARY KEY, chat INTEGER, body TEXT, due REAL, sent INTEGER DEFAULT 0)")

def calc(expr):
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
           ast.Mod: operator.mod, ast.Pow: operator.pow}
    def visit(n):
        if isinstance(n, ast.Expression): return visit(n.body)
        if isinstance(n, ast.Constant) and type(n.value) in (int, float): return n.value
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            v = visit(n.operand); return v if isinstance(n.op, ast.UAdd) else -v
        if isinstance(n, ast.BinOp) and type(n.op) in ops:
            a, b = visit(n.left), visit(n.right)
            if abs(a) > 10**12 or abs(b) > 10**12: raise ValueError()
            if isinstance(n.op, ast.Pow) and (abs(b) > 8 or abs(a) > 10**6): raise ValueError()
            v = ops[type(n.op)](a, b)
            if isinstance(v, (int, float)) and abs(v) > 10**15: raise ValueError()
            return v
        raise ValueError()
    return visit(ast.parse(expr, mode="eval"))

HELP = """🤖 PONEIX | SELF — دستیار شخصی

⏰ /time — ساعت و تاریخ
👤 /me — اطلاعات حساب
🆔 /id — شناسه چت
🧮 /calc 25*4 — ماشین‌حساب
🔤 /upper متن — حروف بزرگ انگلیسی
🔡 /lower متن — حروف کوچک انگلیسی
🔁 /reverse متن — برعکس کردن متن
🔢 /count متن — شمارش کلمات و نویسه‌ها
🎲 /random 1 100 — عدد تصادفی

📝 /note متن — ذخیره یادداشت
📚 /notes — فهرست یادداشت‌ها
🗑 /delnote 1 — حذف یادداشت
☑️ /todo متن — افزودن کار
📋 /todos — فهرست کارها
✅ /done 1 — تکمیل کار
🗑 /deltodo 1 — حذف کار

⏳ /remind 10m متن — یادآور
⏰ /reminders — فهرست یادآورها
🗑 /delremind 1 — حذف یادآور

واحد یادآور: s ثانیه، m دقیقه، h ساعت، d روز.
راهنما: /help"""

def handle(m):
    chat = m.get("chat", {}).get("id")
    if chat is None: return
    text = m.get("text", "").strip()
    if not text: return
    user = m.get("from", {})
    cmd, _, arg = text.partition(" ")
    cmd, arg = cmd.split("@", 1)[0].lower(), arg.strip()
    if cmd in ("/start", "/help"):
        send(chat, "سلام " + user.get("first_name", "") + " 👋\nبه PONEIX خوش آمدی.\n\n" + HELP)
    elif cmd == "/time":
        now = datetime.now(ZoneInfo(TIMEZONE))
        send(chat, "🕒 " + now.strftime("%Y-%m-%d %H:%M:%S") + "\nمنطقه زمانی: " + TIMEZONE)
    elif cmd == "/me":
        send(chat, "👤 شناسه: " + str(user.get("id")) + "\nنام: " + user.get("first_name", "") +
             "\nنام خانوادگی: " + user.get("last_name", "") + "\nنام کاربری: @" + user.get("username", "ندارد"))
    elif cmd == "/id":
        send(chat, "شناسه چت: " + str(chat) + "\nشناسه کاربر: " + str(user.get("id")))
    elif cmd == "/calc":
        try: send(chat, "🧮 نتیجه: " + str(calc(arg)))
        except Exception: send(chat, "عبارت نامعتبر است. نمونه: /calc (12+8)*3")
    elif cmd == "/upper": send(chat, arg.upper() or "متنی وارد کن.")
    elif cmd == "/lower": send(chat, arg.lower() or "متنی وارد کن.")
    elif cmd == "/reverse": send(chat, arg[::-1] or "متنی وارد کن.")
    elif cmd == "/count":
        send(chat, "نویسه‌ها: " + str(len(arg)) + "\nکلمات: " + str(len(arg.split())) if arg else "نمونه: /count سلام دنیا")
    elif cmd == "/random":
        try:
            p = list(map(int, arg.split()))
            lo, hi = (p[0], p[1]) if len(p) == 2 else (1, p[0])
            if lo > hi or hi-lo > 10**9: raise ValueError()
            send(chat, "🎲 " + str(random.randint(lo, hi)))
        except Exception: send(chat, "نمونه: /random 1 100")
    elif cmd == "/note":
        if not arg: send(chat, "نمونه: /note ایده پروژه")
        else:
            with db() as con: cur = con.execute("INSERT INTO notes(chat,body) VALUES(?,?)", (chat,arg))
            send(chat, "یادداشت #" + str(cur.lastrowid) + " ذخیره شد ✅")
    elif cmd == "/notes":
        with db() as con: rows = con.execute("SELECT id,body FROM notes WHERE chat=? ORDER BY id DESC LIMIT 30",(chat,)).fetchall()
        send(chat, "\n".join("#"+str(i)+" — "+b for i,b in rows) if rows else "یادداشتی نداری.")
    elif cmd == "/delnote":
        try:
            with db() as con: cur=con.execute("DELETE FROM notes WHERE id=? AND chat=?",(int(arg),chat))
            send(chat, "حذف شد." if cur.rowcount else "یادداشت پیدا نشد.")
        except Exception: send(chat, "نمونه: /delnote 1")
    elif cmd == "/todo":
        if not arg: send(chat, "نمونه: /todo خرید نان")
        else:
            with db() as con: cur=con.execute("INSERT INTO todos(chat,body) VALUES(?,?)",(chat,arg))
            send(chat, "کار #"+str(cur.lastrowid)+" اضافه شد ✅")
    elif cmd == "/todos":
        with db() as con: rows=con.execute("SELECT id,body,done FROM todos WHERE chat=? ORDER BY done,id DESC LIMIT 50",(chat,)).fetchall()
        send(chat, "\n".join(("✅ " if d else "⬜ ")+"#"+str(i)+" — "+b for i,b,d in rows) if rows else "فهرست کارها خالی است.")
    elif cmd == "/done":
        try:
            with db() as con: cur=con.execute("UPDATE todos SET done=1 WHERE id=? AND chat=?",(int(arg),chat))
            send(chat, "انجام‌شده علامت خورد ✅" if cur.rowcount else "کار پیدا نشد.")
        except Exception: send(chat, "نمونه: /done 1")
    elif cmd == "/deltodo":
        try:
            with db() as con: cur=con.execute("DELETE FROM todos WHERE id=? AND chat=?",(int(arg),chat))
            send(chat, "حذف شد." if cur.rowcount else "کار پیدا نشد.")
        except Exception: send(chat, "نمونه: /deltodo 1")
    elif cmd == "/remind":
        match=re.match(r"^(\d+)([smhd])\s+(.+)$",arg,re.I)
        if not match: send(chat, "نمونه: /remind 10m تماس با دوست")
        else:
            amount,unit,body=int(match.group(1)),match.group(2).lower(),match.group(3)
            seconds=amount*{"s":1,"m":60,"h":3600,"d":86400}[unit]
            if amount<1 or seconds>365*86400: send(chat,"زمان باید بین ۱ ثانیه تا یک سال باشد.")
            else:
                with db() as con: cur=con.execute("INSERT INTO reminders(chat,body,due) VALUES(?,?,?)",(chat,body,time.time()+seconds))
                send(chat,"یادآور #"+str(cur.lastrowid)+" ثبت شد ⏰")
    elif cmd == "/reminders":
        with db() as con: rows=con.execute("SELECT id,body,due FROM reminders WHERE chat=? AND sent=0 ORDER BY due LIMIT 30",(chat,)).fetchall()
        send(chat,"\n".join("#"+str(i)+" — "+b+" ("+datetime.fromtimestamp(d,ZoneInfo(TIMEZONE)).strftime("%m-%d %H:%M")+")" for i,b,d in rows) if rows else "یادآور فعالی نداری.")
    elif cmd == "/delremind":
        try:
            with db() as con: cur=con.execute("DELETE FROM reminders WHERE id=? AND chat=? AND sent=0",(int(arg),chat))
            send(chat,"حذف شد." if cur.rowcount else "یادآور پیدا نشد.")
        except Exception: send(chat,"نمونه: /delremind 1")
    elif cmd == "/format": send(chat,arg or "متنی وارد کن.")
    else: send(chat,"دستور ناشناخته است. /help را بفرست.")

def main():
    init_db()
    print("PONEIX | SELF started")
    offset=0
    while True:
        try:
            with db() as con:
                due=con.execute("SELECT id,chat,body FROM reminders WHERE sent=0 AND due<=?",(time.time(),)).fetchall()
                for rid,chat,body in due:
                    send(chat,"⏰ یادآوری:\n"+body)
                    con.execute("UPDATE reminders SET sent=1 WHERE id=?",(rid,))
            updates=api("getUpdates",{"offset":offset,"timeout":25})
            for update in updates:
                offset=update["update_id"]+1
                if "message" in update:
                    try: handle(update["message"])
                    except Exception as e: print("Message error:",repr(e))
        except KeyboardInterrupt: break
        except Exception as e:
            print("Polling error:",repr(e)); time.sleep(5)

if __name__ == "__main__":
    main()
