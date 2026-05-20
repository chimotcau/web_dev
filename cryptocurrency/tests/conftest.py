import pytest


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    from app import create_app, db

    flask_app = create_app()
    flask_app.config.update(TESTING=True)

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register_and_login(client):
    client.post(
        "/register",
        data={
            "username": "tester",
            "email": "tester@example.com",
            "password": "password123",
        },
        follow_redirects=True,
    )

    return client.post(
        "/login",
        data={
            "email": "tester@example.com",
            "password": "password123",
        },
        follow_redirects=True,
    )
