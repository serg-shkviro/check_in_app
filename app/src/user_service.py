from flask import session
from app.models import User
from app import db


class UserService:
    @staticmethod
    def create_user(name, email, password, confirm_password):
        if User.query.filter_by(email=email).first():
            raise ValueError('Такой email уже зарегистрирован')

        if not all([name, email, password, confirm_password]):
            raise ValueError('Не все поля заполнены')

        if password != confirm_password:
            raise ValueError('Пароли не совпадают')

        if len(password) < 8:
            raise ValueError('Пароль должен содержать не менее 8 символов')

        user = User(name=name, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return user

    @staticmethod
    def login_user(email, password):
        if not email or not password:
            raise ValueError('Заполните все поля')

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            raise ValueError('Неверный email или пароль')

        return user

    @staticmethod
    def get_user_by_email(email):
        user = User.query.filter_by(email=email).first()
        if user:
            return {'id': user.id, 'name': user.name, 'email': user.email}
        return None
