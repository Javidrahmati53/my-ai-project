import os, json, time, urllib.request, urllib.parse, ast, operator
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.getenv("BOT_TOKEN", "").strip()
TZ = os.getenv("TIMEZONE", "Asia/Baku")
if not TOKEN:
    raise SystemExit("Set BOT_TOKEN in your hosting environment.")

API = "https://api.telegram.org/bot" + TOKEN + "/"

def api(method, params=None):
    data = urllib.parse.urlencode(params or {}).encode()
    req = urllib.request.Request(API + method, data=data)
    with urllib.request.urlopen(req, timeout=45) as response:
        payload = json.loads(response.read().decode())
    if not payload.get("ok"):
        raise RuntimeError(payload.get("description", "Telegram API error"))
    return payload["result"]

def send(chat_id, text):
    api("sendMessage", {"chat_id": chat_id, "text": text})

def safe_calc(expression):
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod}
    def visit(node):
        if isinstance(node, ast.Expression): return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float): return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            val = visit(node.operand)
            return val if isinstance(node.op, ast.UAdd) else -val
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 8: raise ValueError("exponent limit")
            return ops[type(node.op)](left, right)
        raise ValueError("unsupported expression")
    return visit(ast.parse(expression, mode="eval"))

def handle(message):
    chat_id = message.get("chat", {}).get("id")
    if chat_id is None: return
    text = message.get("text", "")
    user = message.get("from", {})
    command, _, argument = text.partition(" ")
    command = command.split("@", 1)[0].lower()
    argument = argument.strip()
    if command in ("/start", "/help"):
        send(chat_id, "PONEIX | SELF\nCommands: /time, /me, /calc <expression>, /format <text>")
    elif command == "/time":
        send(chat_id, datetime.now(ZoneInfo(TZ)).strftime("%Y-%m-%d %H:%M:%S") + " (" + TZ + ")")
    elif command == "/me":
        send(chat_id, f"ID: {user.get('id')}\nName: {user.get('first_name','')}\nUsername: @{user.get('username','none')}")
    elif command == "/calc":
        try: send(chat_id, str(safe_calc(argument)))
        except Exception: send(chat_id, "Invalid expression. Example: /calc 2+3*4")
    elif command == "/format":
        send(chat_id, argument)
    else:
        send(chat_id, "Unknown command. Send /help")

def main():
    print("PONEIX bot started. Ctrl+C to stop.")
    offset = 0
    while True:
        try:
            updates = api("getUpdates", {"offset": offset, "timeout": 30})
            for update in updates:
                offset = update["update_id"] + 1
                if "message" in update:
                    handle(update["message"])
        except KeyboardInterrupt:
            break
        except Exception as error:
            print("Polling error:", error)
            time.sleep(5)

if __name__ == "__main__":
    main()
