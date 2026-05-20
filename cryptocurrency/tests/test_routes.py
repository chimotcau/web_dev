from app.models import Transaction, Watchlist

from .conftest import register_and_login


def test_home_page_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Crypto" in response.data


def test_register_login_and_dashboard(client):
    response = register_and_login(client)

    assert response.status_code == 200
    assert b"Portfolio" in response.data or b"Dashboard" in response.data


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")

    assert response.status_code in (302, 401)
    assert "/login" in response.location


def test_market_data_api_returns_json(client, monkeypatch):
    import app.routes as routes

    register_and_login(client)
    monkeypatch.setattr(routes, "get_live_price", lambda symbol: 100.0)

    response = client.get("/api/market-data")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    assert data[0]["symbol"] == "BTC"
    assert data[0]["price"] == 100.0


def test_add_transaction(client):
    register_and_login(client)

    response = client.post(
        "/transactions/new",
        data={
            "type": "BUY",
            "symbol": "BTC",
            "quantity": "1.5",
            "price": "50000",
            "fee": "0",
            "timestamp": "2026-05-20",
            "exchange": "BYBIT",
            "note": "test transaction",
        },
        follow_redirects=True,
    )

    tx = Transaction.query.filter_by(symbol="BTC").first()

    assert response.status_code == 200
    assert tx is not None
    assert tx.quantity == 1.5


def test_toggle_watchlist(client):
    register_and_login(client)

    response = client.post("/watchlist/toggle/BTC")
    data = response.get_json()

    item = Watchlist.query.filter_by(symbol="BTC").first()

    assert response.status_code == 200
    assert data["watched"] is True
    assert item is not None

    second_response = client.post("/watchlist/toggle/BTC")
    second_data = second_response.get_json()

    item_after_remove = Watchlist.query.filter_by(symbol="BTC").first()

    assert second_response.status_code == 200
    assert second_data["watched"] is False
    assert item_after_remove is None
