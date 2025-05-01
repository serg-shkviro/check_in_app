from app.models import Marker
from .user_service import User
from app import db


class MarkerService:
    @staticmethod
    def create_marker(user_email, password_hash, **kwargs):
        user = User.query.filter_by(email=user_email).first()

        if not user or not user.check_hash_and_hash(password_hash):
            raise ValueError('Неверный пароль')

        required_fields = {'latitude', 'longitude', 'title', 'date_time'}
        if not required_fields.issubset(kwargs.keys()):
            missing = required_fields - set(kwargs.keys())
            raise ValueError(f'Отсутствуют обязательные поля: {missing}')

        marker = Marker(
            user_id=user.id,
            latitude=kwargs['latitude'],
            longitude=kwargs['longitude'],
            title=kwargs['title'],
            date_time=kwargs['date_time']
        )
        db.session.add(marker)
        db.session.commit()

        return marker

    @staticmethod
    def edit_marker(marker_id, user_email, password_hash,  **kwargs):
        user = User.query.filter_by(email=user_email).first()

        if not user or not user.check_hash_and_hash(password_hash):
            raise ValueError('Неверный пароль')

        marker = Marker.query.filter_by(id=marker_id, user_id=user.id).first()
        if not marker:
            raise ValueError(
                'Маркер не найден или не принадлежит пользователю')

        allowed_fields = {'latitude', 'longitude', 'title', 'date_time'}
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(marker, field, value)

        db.session.commit()
        return marker

    @staticmethod
    def get_all(user_email, password_hash):
        user = User.query.filter_by(email=user_email).first()

        if not user or not user.check_hash_and_hash(password_hash):
            raise ValueError('Неверный пароль')

        if user.id:
            return Marker.query.filter_by(user_id=user.id).all()
        raise ValueError('Неверный пользователь')

    @staticmethod
    def delete_marker(marker_id, user_email, password_hash):
        user = User.query.filter_by(email=user_email).first()

        if not user or not user.check_hash_and_hash(password_hash):
            raise ValueError('Неверный пароль')

        marker = Marker.query.filter_by(id=marker_id, user_id=user.id).first()
        if not marker:
            raise ValueError(
                'Маркер не найден или не принадлежит пользователю')

        db.session.delete(marker)
        db.session.commit()
        return True
