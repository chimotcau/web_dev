from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        database_url or "sqlite:///portfolio.db"
    )
    
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "mysecretkey"

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = "main.login"

    from .models import Transaction, PriceCache, User, Watchlist

    from .routes import main
    app.register_blueprint(main)

    return app


@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))