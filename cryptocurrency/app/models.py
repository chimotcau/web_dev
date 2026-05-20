from datetime import datetime

from flask_login import UserMixin

from . import db


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)  # BUY or SELL
    symbol = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    fee = db.Column(db.Float, default=0.0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    exchange = db.Column(db.String(50))
    note = db.Column(db.String(200))

    # Reserved for future exchange imports.
    external_source = db.Column(db.String(50))
    external_id = db.Column(db.String(100))

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


class PriceCache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(50), default="bybit")


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    transactions = db.relationship("Transaction", backref="user", lazy=True)


class Watchlist(db.Model):
    __table_args__ = (
        db.UniqueConstraint("user_id", "symbol", name="uq_watchlist_user_symbol"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
