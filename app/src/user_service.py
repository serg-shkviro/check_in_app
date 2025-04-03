from flask import session
from app.models import User
from app import db


class UserService:
    @staticmethod
    def create_user(name, email, password, confirm_password):
        if User.query.filter_by(email=email).first():
            raise ValueError('Такой email уже зарегестрирован')

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

        UserService.save_session(user)

        return user

    @staticmethod
    def login_user(email, password):
        if not email or not password:
            raise ValueError('Заполните все поля')

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            raise ValueError('Неверный email или пароль')

        UserService.save_session(user)

        return user

    @staticmethod
    def save_session(user):
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.name

    @staticmethod
    def delete_session():
        session.pop('user_id', None)
        session.pop('user_email', None)
        session.pop('user_name', None)

    @staticmethod
    def get_current_user():
        """Получает текущего пользователя из сессии."""
        user_id = session.get('user_id')
        if not user_id:
            return None
        return {'id': session['user_id'], 'name': session['user_name'], 'email': session['user_email']}
