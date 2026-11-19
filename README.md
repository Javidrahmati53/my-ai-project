# PONEIX | SELF — Personal Telegram Assistant v1.0

A Persian-language Telegram bot built with Python's standard library. No pip packages are required.

## Features and commands

- `/start`, `/help` — welcome and command guide
- `/time` — date and time in the configured timezone (default: Asia/Baku)
- `/me`, `/id` — Telegram profile and chat identifiers
- `/calc 25*4` — safe arithmetic calculator
- `/upper text`, `/lower text`, `/reverse text`, `/count text`, `/format text` — text utilities
- `/random 1 100` — random number
- `/note text`, `/notes`, `/delnote 1` — notes
- `/todo text`, `/todos`, `/done 1`, `/deltodo 1` — task list
- `/remind 10m text`, `/reminders`, `/delremind 1` — reminders (s/m/h/d)

## Run

Python 3.12+:

```bash
python main.py
```

Set `BOT_TOKEN` as an environment variable. Set `TIMEZONE` optionally; default is `Asia/Baku`.

## GitHub Actions

The workflow in `.github/workflows/poneix.yml` starts the bot manually or on a six-hour schedule. Add a repository Actions secret named `BOT_TOKEN` containing the Telegram bot token.

GitHub-hosted runners are temporary and a job is time-limited. Local SQLite notes, tasks, and reminders are stored on the runner and can be lost when that runner stops; this setup is a free test deployment, not permanent 24/7 hosting. For durable storage and continuous uptime, use a persistent host and persistent database.

## Scope

This is a Telegram bot, not an automation of a personal Telegram user account. It responds to commands sent to the bot.
