# Crypto Portfolio Manager

A Flask web application for tracking personal cryptocurrency transactions, portfolio value, watchlist, realtime market prices, candlestick charts, and profit/loss analytics.

## Features

- User registration, login, and logout
- User-specific transactions and portfolio dashboard
- BUY / SELL transaction CRUD
- Advanced transaction filters, date filters, sorting, and CSV export
- FIFO-based realized PnL and remaining cost basis
- Live public Bybit prices with local cache
- Realtime market page with search and sorting
- Candlestick charts using Bybit kline data
- Watchlist
- Portfolio allocation donut chart
- Portfolio statistics: trade count, buy/sell volume, ROI, best/worst coin
- Docker and Docker Compose support
- Unit tests with pytest
- CI/CD for tests and linter with GitHub Actions
- Pre-commit lint hook

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Migrate / Alembic
- Flask-Login
- SQLite for local development
- PostgreSQL-ready deployment via `DATABASE_URL`
- Chart.js and lightweight-charts on the frontend
- Docker / Docker Compose
- pytest
- ruff
- GitHub Actions

## Project Structure

```text
web_dev/
├── .github/workflows/
├── cryptocurrency/
│   ├── app/
│   ├── migrations/
│   ├── tests/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── run.py
├── .pre-commit-config.yaml
├── pyproject.toml
├── render.yaml
└── README.md
```

## Local Setup

```powershell
cd cryptocurrency
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
python -m flask --app run.py db upgrade
python run.py
```

Open:

```text
http://127.0.0.1:5000/
```

## Run Tests

```powershell
cd cryptocurrency
pytest -q
```

## Run Linter

From repository root:

```powershell
ruff check cryptocurrency
```

## Pre-commit

Install and enable hooks:

```powershell
cd cryptocurrency
pip install -r requirements-dev.txt
cd ..
pre-commit install
```

Run manually:

```powershell
pre-commit run --all-files
```

## Docker

Run with Docker Compose:

```powershell
cd cryptocurrency
docker compose up --build
```

Open:

```text
http://localhost:5000/
```

Stop containers:

```powershell
docker compose down
```

Stop and remove PostgreSQL volume:

```powershell
docker compose down -v
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/market-data` | Returns realtime market prices for supported coins |
| GET | `/api/kline/<symbol>` | Returns candlestick/kline data for a symbol |
| GET | `/api/pnl-chart` | Returns current user's PnL chart data |
| GET | `/api/preview-market` | Returns market preview prices for homepage |
| POST | `/watchlist/toggle/<symbol>` | Adds/removes a coin from current user's watchlist |
| GET | `/export/csv` | Exports current user's transactions as CSV |

## Deployment

The app reads `DATABASE_URL` automatically. For PostgreSQL providers that expose `postgres://...`, the app converts it to `postgresql://...`.

Set a strong production `SECRET_KEY`.

A `render.yaml` file is included for Render deployment. After creating the web service, add the public URL to the grading form.

## Do Not Commit

The repository ignores local database and cache files:

- `instance/`
- `*.db`
- `__pycache__/`
- `.env`
- virtual environments
