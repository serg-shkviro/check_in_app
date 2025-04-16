from flask import request, jsonify, render_template, redirect, url_for
from flasgger import swag_from
from dateutil.parser import isoparse
from .src.user_service import UserService
from .src.marker_service import MarkerService

def init_routes(app):
    @app.route('/login')
    @swag_from({
        'responses': {
            200: {
                'description': 'Страница входа'
            }
        }
    })
    def login():
         return render_template('login.html')
    
    @app.route('/register')
    @swag_from({
        'responses': {
            200: {
                'description': 'Страница регистрации'
            }
        }
    })
    def register():
        return render_template('register.html')

    @app.route('/map')
    @swag_from({
        'responses': {
            200: {'description': 'Карта для авторизованных пользователей'},
            302: {'description': 'Редирект на логин при отсутствии сессии'}
        }
    })
    def map():
        if UserService.get_current_user() is None:
            return redirect(url_for('login'))
        return render_template('map.html')

    @app.route('/get_user', methods=['GET'])
    @swag_from({
        'responses': {
            200: {
                'description': 'Возвращает текущего пользователя',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'user': {'type': 'object'}
                    }
                }
            },
            401: {'description': 'Пользователь не авторизован'}
        }
    })
    def get_user():
        user = UserService.get_current_user()
        if not (user is None):
            return jsonify({'user': user})
        else:
            return jsonify({'user': None}), 401

    @app.route('/sing_up', methods=['POST'])
    @swag_from({
        'parameters': [
            {
                'name': 'body',
                'in': 'body',
                'required': True,
                'schema': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'email': {'type': 'string'},
                        'password': {'type': 'string'},
                        'confirmPassword': {'type': 'string'}
                    }
                }
            }
        ],
        'responses': {
            201: {'description': 'Пользователь создан'},
            400: {'description': 'Ошибка валидации'}
        }
    })
    def sing_up():
        data = request.get_json()
        try:
            user = UserService.create_user(
                name=data['name'],
                email=data['email'],
                password=data['password'],
                confirm_password=data['confirmPassword']
            )
            return jsonify({"message": "User created", "user_id": user.id}), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/sing_in', methods=['POST'])
    @swag_from({
        'parameters': [
            {
                'name': 'body',
                'in': 'body',
                'required': True,
                'schema': {
                    'type': 'object',
                    'properties': {
                        'email': {'type': 'string'},
                        'password': {'type': 'string'}
                    }
                }
            }
        ],
        'responses': {
            200: {'description': 'Успешный вход'},
            400: {'description': 'Ошибка авторизации'}
        }
    })
    def sing_in():
        data = request.get_json()
        try:
            user = UserService.login_user(
                email=data['email'],
                password=data['password']
            )
            return jsonify({'message': 'Успешный вход', 'name': user.name}), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/logout')
    @swag_from({
        'responses': {
            302: {'description': 'Редирект на логин'}
        }
    })
    def logout():
        UserService.delete_session()
        return redirect(url_for('login'))

    @app.route('/add_marker', methods=['POST'])
    @swag_from({
        'parameters': [
            {
                'name': 'body',
                'in': 'body',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'user_email': {'type': 'string'},
                        'password': {'type': 'string'},
                        'latitude': {'type': 'number'},
                        'longitude': {'type': 'number'},
                        'title': {'type': 'string'},
                        'date_time': {'type': 'string', 'format': 'date-time'}
                    }
                }
            }
        ],
        'responses': {
            201: {'description': 'Маркер добавлен'},
            400: {'description': 'Ошибка'}
        }
    })
    def add_marker():
        data = request.get_json()
        try:
            marker = MarkerService.create_marker(
                user_email=data['user_email'],
                password=data['password'],
                latitude=data['latitude'],
                longitude=data['longitude'],
                title=data['title'],
                date_time=isoparse(data['date_time'])
            )
            return jsonify({"message": "Marker created", "marker_id": marker.id}), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/edit_marker', methods=['POST'])
    @swag_from({
        'parameters': [
            {
                'name': 'body',
                'in': 'body',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'marker_id': {'type': 'integer'},
                        'user_email': {'type': 'string'},
                        'password': {'type': 'string'},
                        'latitude': {'type': 'number'},
                        'longitude': {'type': 'number'},
                        'title': {'type': 'string'}
                    }
                }
            }
        ],
        'description': 'По сути PATCH, но реализован как POST',
        'responses': {
            201: {'description': 'Маркер отредактирован'},
            400: {'description': 'Ошибка'}
        }
    })
    def edit_marker():
        data = request.get_json()
        try:
            marker = MarkerService.edit_marker(
                marker_id=data['marker_id'],
                user_email=data['user_email'],
                password=data['password'],
                latitude=data['latitude'],
                longitude=data['longitude'],
                title=data['title']
            )
            return jsonify({"message": "Marker edited", "marker_id": marker.id}), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/get_markers', methods=['POST'])
    @swag_from({
        'parameters': [
            {
                'name': 'body',
                'in': 'body',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'user_email': {'type': 'string'},
                        'password': {'type': 'string'}
                    }
                }
            }
        ],
        'description': 'По сути GET, но реализован как POST',
        'responses': {
            201: {
                'description': 'Список маркеров',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'markers': {
                            'type': 'array',
                            'items': {'type': 'object'}
                        }
                    }
                }
            },
            400: {'description': 'Ошибка'}
        }
    })
    def get_markers():
        data = request.get_json()
        try:
            markers = MarkerService.get_all(
                user_email=data['user_email'],
                password=data['password'],
            )
            return jsonify({"markers": [marker.to_dict() for marker in markers]}), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/delete_marker', methods=['POST'])
    @swag_from({
        'parameters': [
            {
                'name': 'body',
                'in': 'body',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'marker_id': {'type': 'integer'},
                        'user_email': {'type': 'string'},
                        'password': {'type': 'string'}
                    }
                }
            }
        ],
        'description': 'По сути DELETE, но реализован как POST',
        'responses': {
            201: {'description': 'Маркер удалён'},
            400: {'description': 'Ошибка'}
        }
    })
    def delete_marker():
        data = request.get_json()
        try:
            result = MarkerService.delete_marker(
                marker_id=data['marker_id'],
                user_email=data['user_email'],
                password=data['password']
            )
            return jsonify({"message": "Marker delete", "result": result}), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
