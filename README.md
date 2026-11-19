# PONEIX | SELF — Android-friendly Bot API version

This project is a simple Telegram bot using Python's standard library only.
No Termux, pip installs, Rust, or native compilation are required to run it
on a regular Python host.

## Commands
- /start or /help — help
- /time — local time
- /me — Telegram user details
- /calc 2+3*4 — safe calculator (limited operators)
- /format text — echo text

## Run on a Python host
Set environment variables:
- BOT_TOKEN: token from BotFather (keep secret; do not commit it)
- TIMEZONE: default Asia/Baku

Then run:
`python main.py`

For cloud hosting, create a worker/background service with the start command
`python main.py` and add BOT_TOKEN as a private environment variable.
Do not put a real bot token in this public repository.

This is a minimal Bot API bot; it cannot act as your personal Telegram account.
