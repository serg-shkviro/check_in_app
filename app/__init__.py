from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import os

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SECRET_KEY'] = 'supersecretkey'
    app.config['SESSION_TYPE'] = 'filesystem'  # Сессии хранятся на сервере
    Session(app)

    db.init_app(app)

    from .routes import init_routes
    init_routes(app)

    with app.app_context():
        if not os.path.exists('users.db'):
            db.create_all()
            print("База данных создана.")

    return app
