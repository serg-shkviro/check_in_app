from flask import request, jsonify, render_template, redirect, url_for
from flasgger import swag_from
from dateutil.parser import isoparse
from .src.user_service import UserService
from flask_bcrypt import check_password_hash
from app.models import User
from .src.marker_service import MarkerService
from flask_jwt_extended import jwt_required, get_jwt_identity, unset_jwt_cookies, create_access_token, get_jwt

def init_routes(app):
    @app.route('/login')
    @swag_from({
        'tags': ['Pages'],
        'summary': 'Страница входа',
        'description': 'Отображает HTML-страницу формы входа. Никакой логики авторизации не выполняется — только возврат шаблона.',
        'responses': {
            200: {
                'description': 'HTML-страница входа успешно возвращена.'
            }
        }
    })
    def login():
         return render_template('login.html')
    
    @app.route('/register')
    @swag_from({
        'tags': ['Pages'],
        'summary': 'Страница регистрации',
        'description': 'Отображает HTML-страницу с формой регистрации нового пользователя. Сервер не выполняет никаких операций — только возвращает шаблон.',
        'responses': {
            200: {
                'description': 'HTML-страница регистрации успешно возвращена.'
            }
        }
    })
    def register():
        return render_template('register.html')

    @app.route('/map')
    @swag_from({
        'tags': ['Pages'],
        'summary': 'Карта для авторизованных пользователей',
        'description': (
            'Возвращает HTML-страницу с картой для авторизованных пользователей. '
            'Требуется наличие валидного JWT токена. '
            'На основе токена извлекается email текущего пользователя. '
            'Если пользователь с таким email не найден, возвращается ошибка 404. '
            'Если токен отсутствует или недействителен, произойдёт редирект на страницу логина.'
        ),
        'security': [{'BearerAuth': []}],
        'responses': {
            200: {
                'description': 'HTML-страница с картой успешно возвращена.'
            },
            401: {
                'description': 'Missing Authorization Header.'
            },
            404: {
                'description': 'Пользователь с таким email не найден.'
            }
        }
    })
    @jwt_required()
    def map():
        current_user_email = get_jwt_identity()
        user = UserService.get_user_by_email(current_user_email)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return render_template('map.html', user=user)

    @app.route('/get_user', methods=['GET'])
    @jwt_required()
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
        current_user_email = get_jwt_identity()
        user = UserService.get_user_by_email(current_user_email)

        if user:
            return jsonify({'user': user})
        else:
            return jsonify({'user': None}), 401

    @app.route('/sing_up', methods=['POST'])
    @swag_from({
        'tags': ['Authentication'],
        'summary': 'Регистрация нового пользователя',
        'description': 'Создаёт нового пользователя по переданным данным. '
                    'При успешной регистрации возвращает JWT-токен. '
                    'Если валидация не пройдена (например, email уже существует или пароли не совпадают), возвращается ошибка.',
        'parameters': [
            {
                'name': 'body',
                'in': 'body',
                'required': True,
                'schema': {
                    'type': 'object',
                    'required': ['name', 'email', 'password', 'confirmPassword'],
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'Имя пользователя'
                        },
                        'email': {
                            'type': 'string',
                            'format': 'email',
                            'description': 'Уникальный email пользователя'
                        },
                        'password': {
                            'type': 'string',
                            'format': 'password',
                            'description': 'Пароль'
                        },
                        'confirmPassword': {
                            'type': 'string',
                            'format': 'password',
                            'description': 'Повтор пароля'
                        }
                    }
                }
            }
        ],
        'responses': {
            201: {
                'description': 'Пользователь успешно зарегистрирован. Возвращается token.',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'access_token': {
                            'type': 'string',
                            'description': 'JWT токен для доступа к защищённым маршрутам'
                        }
                    }
                }
            },
            400: {
                'description': 'Ошибка валидации. Возможные причины: пустые поля, email уже зарегистрирован, пароли не совпадают.',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'error': {
                            'type': 'string'
                        }
                    }
                }
            }
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

            access_token = create_access_token(identity=user.email, additional_claims={"password": user.password_hash})

            return jsonify(access_token=access_token), 201

        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/sing_in', methods=['POST'])
    @swag_from({
        'tags': ['Authentication'],
        'summary': 'Авторизация пользователя',
        'description': 'Проверяет email и пароль пользователя. '
                    'В случае успеха возвращает JWT-token. '
                    'При неверных данных выбрасывается ошибка авторизации.',
        'parameters': [
            {
                'name': 'body',
                'in': 'body',
                'required': True,
                'schema': {
                    'type': 'object',
                    'required': ['email', 'password'],
                    'properties': {
                        'email': {
                            'type': 'string',
                            'format': 'email',
                            'description': 'Email пользователя'
                        },
                        'password': {
                            'type': 'string',
                            'format': 'password',
                            'description': 'Пароль пользователя'
                        }
                    }
                }
            }
        ],
        'responses': {
            200: {
                'description': 'Успешная авторизация. Возвращается access token.',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'access_token': {
                            'type': 'string',
                            'description': 'JWT токен для доступа к защищённым маршрутам'
                        }
                    }
                }
            },
            403: {
                'description': 'Ошибка авторизации. Неверный email или пароль.',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'error': {
                            'type': 'string'
                        }
                    }
                }
            }
        }
    })
    def sing_in():
        data = request.get_json()

        try:
            user = UserService.login_user(
                email=data['email'],
                password=data['password']
            )

            access_token = create_access_token(identity=user.email, additional_claims={"password": user.password_hash})

            return jsonify(access_token=access_token), 200

        except ValueError as e:
            return jsonify({"error": str(e)}), 403

    @app.route('/logout')
    @jwt_required()
    @swag_from({
        'tags': ['Authentication'],
        'summary': 'Выход из системы',
        'description': 'Удаляет текущий JWT токен из cookies и выполняет редирект на страницу логина.',
        'responses': {
            302: {
                'description': 'Успешный выход. Редирект на страницу логина.'
            }
        }
    })
    def logout():
        unset_jwt_cookies()
        return redirect(url_for('login'))

    @app.route('/add_marker', methods=['POST'])
    @jwt_required()
    @swag_from({
        'tags': ['Markers'],
        'summary': 'Добавление маркера на карту',
        'description': 'Этот эндпоинт позволяет пользователю добавить новый маркер на карту, предоставив координаты, заголовок и дату/время. Перед добавлением маркера выполняется проверка на валидность пароля, а также проверка наличия пользователя и хэшированного пароля в JWT.',
        'parameters': [
            {
                'in': 'body',
                'name': 'marker',
                'required': True,
                'schema': {
                    'type': 'object',
                    'properties': {
                        'latitude': {
                            'type': 'number',
                            'description': 'Широта маркера на карте',
                            'example': 55.7558
                        },
                        'longitude': {
                            'type': 'number',
                            'description': 'Долгота маркера на карте',
                            'example': 37.6173
                        },
                        'title': {
                            'type': 'string',
                            'description': 'Заголовок маркера',
                            'example': 'Новое место'
                        },
                        'date_time': {
                            'type': 'string',
                            'format': 'date-time',
                            'description': 'Дата и время добавления маркера',
                            'example': '2025-05-01T14:00:00Z'
                        }
                    }
                }
            }
        ],
        'responses': {
            201: {
                'description': 'Маркер успешно добавлен',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string', 'example': 'Marker created'},
                        'marker_id': {'type': 'integer', 'example': 1}
                    }
                }
            },
            400: {
                'description': 'Ошибка при добавлении маркера, возможно, неверный формат данных или ошибка валидации'
            },
            404: {
                'description': 'Пользователь не найден'
            },
            401: {
                'description': 'Ошибка аутентификации, пользователь не авторизован'
            }
        }
    })
    def add_marker():
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()
        user_password_hash = get_jwt()['password']

        if not user_password_hash:
            return jsonify({"error": "Password hash not provided"}), 401

        if not user.check_hash_and_hash(user_password_hash):
            return jsonify({"error": "Invalid password"}), 401

        try:
            marker = MarkerService.create_marker(
                user_email=current_user_email,
                password_hash=user_password_hash,
                latitude=data['latitude'],
                longitude=data['longitude'],
                title=data['title'],
                date_time=isoparse(data['date_time'])
            )

            return jsonify({"message": "Marker created", "marker_id": marker.id}), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/edit_marker', methods=['PATCH'])
    @jwt_required()
    @swag_from({
        'tags': ['Markers'],
        'summary': 'Редактирование маркера на карте',
        'description': 'Этот эндпоинт позволяет пользователю редактировать маркер на карте, предоставив его ID и обновленные данные, такие как координаты, заголовок. Перед редактированием маркера выполняется проверка на валидность пароля, а также проверка наличия пользователя и хэшированного пароля в JWT.',
        'parameters': [
            {
                'in': 'body',
                'name': 'marker',
                'required': True,
                'schema': {
                    'type': 'object',
                    'properties': {
                        'marker_id': {
                            'type': 'integer',
                            'description': 'ID маркера, который необходимо отредактировать',
                            'example': 1
                        },
                        'latitude': {
                            'type': 'number',
                            'description': 'Новая широта маркера на карте',
                            'example': 55.7558
                        },
                        'longitude': {
                            'type': 'number',
                            'description': 'Новая долгота маркера на карте',
                            'example': 37.6173
                        },
                        'title': {
                            'type': 'string',
                            'description': 'Новый заголовок маркера',
                            'example': 'Обновленное место'
                        }
                    }
                }
            }
        ],
        'responses': {
            200: {
                'description': 'Маркер успешно отредактирован',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string', 'example': 'Marker edited'},
                        'marker_id': {'type': 'integer', 'example': 1}
                    }
                }
            },
            400: {
                'description': 'Ошибка при редактировании маркера, возможно, неверный формат данных или ошибка валидации'
            },
            404: {
                'description': 'Пользователь не найден'
            },
            401: {
                'description': 'Ошибка аутентификации, пользователь не авторизован'
            }
        }
    })
    def edit_marker():
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()
        user_password_hash = get_jwt()['password']

        if not user_password_hash:
            return jsonify({"error": "Password hash not provided"}), 401

        if not user.check_hash_and_hash(user_password_hash):
            return jsonify({"error": "Invalid password"}), 401

        try:
            marker = MarkerService.edit_marker(
                marker_id=data['marker_id'],
                user_email=current_user_email,
                password_hash=user_password_hash,
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                title=data.get('title')
            )

            return jsonify({"message": "Marker edited", "marker_id": marker.id}), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/get_markers', methods=['GET'])
    @jwt_required()
    @swag_from({
        'tags': ['Markers'],
        'summary': 'Получение списка маркеров текущего пользователя',
        'description': 'Этот эндпоинт возвращает список всех маркеров, принадлежащих текущему пользователю. Информация о пользователе извлекается из JWT, и перед тем как вернуть маркеры, проверяется, что хэш пароля в JWT совпадает с хэшем пароля пользователя в базе данных.',
        'responses': {
            200: {
                'description': 'Список маркеров текущего пользователя',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'markers': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'id': {'type': 'integer', 'example': 1},
                                    'latitude': {'type': 'number', 'example': 55.7558},
                                    'longitude': {'type': 'number', 'example': 37.6173},
                                    'title': {'type': 'string', 'example': 'Маркер 1'},
                                    'date_time': {'type': 'string', 'format': 'date-time', 'example': '2023-05-01T10:00:00Z'}
                                }
                            }
                        }
                    }
                }
            },
            400: {
                'description': 'Ошибка получения маркеров, возможно, из-за ошибки сервера или неверного запроса'
            },
            401: {
                'description': 'Пользователь не авторизован или неверный пароль'
            },
            404: {
                'description': 'Пользователь не найден'
            }
        }
    })
    def get_markers():
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        user_password_hash = get_jwt()['password']

        if not user_password_hash:
            return jsonify({"error": "Password hash not provided"}), 401

        if not user.check_hash_and_hash(user_password_hash):
            return jsonify({"error": "Invalid password"}), 401

        try:
            markers = MarkerService.get_all(user_email=current_user_email, password_hash=user_password_hash)
            return jsonify({"markers": [marker.to_dict() for marker in markers]}), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/delete_marker', methods=['DELETE'])
    @jwt_required()
    @swag_from({
        'tags': ['Markers'],
        'summary': 'Удаление маркера по ID',
        'description': 'Этот эндпоинт удаляет маркер текущего пользователя, если пользователь авторизован. Данные пользователя извлекаются из JWT, и перед удалением маркера проверяется, что хэш пароля в JWT совпадает с хэшем пароля пользователя.',
        'parameters': [
            {
                'name': 'marker_id',
                'in': 'query',
                'required': True,
                'type': 'integer',
                'description': 'ID маркера, который необходимо удалить'
            }
        ],
        'responses': {
            200: {
                'description': 'Маркер успешно удален',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string', 'example': 'Marker deleted'},
                        'result': {'type': 'string'}
                    }
                }
            },
            400: {
                'description': 'Ошибка удаления маркера или отсутствие маркера с указанным ID'
            },
            401: {
                'description': 'Пользователь не авторизован или неверный пароль'
            },
            404: {
                'description': 'Пользователь не найден'
            }
        }
    })
    def delete_marker():
        marker_id = request.args.get('marker_id', type=int)

        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        user_password_hash = get_jwt()['password']

        if not user_password_hash:
            return jsonify({"error": "Password hash not provided"}), 401

        if not user.check_hash_and_hash(user_password_hash):
            return jsonify({"error": "Invalid password"}), 401

        if marker_id is None:
            return jsonify({"error": "marker_id is required"}), 400

        try:
            result = MarkerService.delete_marker(
                marker_id=marker_id,
                user_email=current_user_email,
                password_hash=user_password_hash
            )
            return jsonify({"message": "Marker deleted", "result": result}), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
