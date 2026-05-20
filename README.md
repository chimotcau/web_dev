# Crypto Portfolio Manager

A Flask web application for tracking personal cryptocurrency transactions, portfolio value, and profit/loss.

## Features

- User registration and login
- User-specific transactions and portfolio dashboard
- BUY / SELL transaction CRUD
- Transaction filters, date filters, sorting, and CSV export
- FIFO-based realized P&L and remaining cost basis
- Live public Bybit prices with local cache
- Realtime market page with search and sorting
- Candlestick charts using Bybit kline data
- Watchlist
- Portfolio allocation chart
- Portfolio statistics: trade count, volumes, ROI, best/worst coin

## Tech Stack

- Flask
- Flask-SQLAlchemy
- Flask-Migrate / Alembic
- Flask-Login
- SQLite for local development
- PostgreSQL-ready deployment via `DATABASE_URL`
- Chart.js and lightweight-charts on the frontend

## Local Setup

```powershell
cd cryptocurrency
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m flask --app run.py db upgrade
python run.py
```

Open:

```text
http://127.0.0.1:5000/
```

## Deployment Notes

The app reads `DATABASE_URL` automatically. For PostgreSQL providers that expose `postgres://...`, the app converts it to `postgresql://...`.

Set a strong `SECRET_KEY` in production.

## Do Not Commit

The repository ignores local database and cache files:

- `instance/`
- `*.db`
- `__pycache__/`
- `.env`
- virtual environments
