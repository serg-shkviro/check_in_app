from flask import render_template, request, jsonify, session, redirect, url_for
from .src.user_service import UserService
from .src.marker_service import MarkerService
from dateutil.parser import isoparse


def init_routes(app):
    @app.route('/')
    def home():
        # Перенаправляем на страницу входа
        return render_template('login.html')

    @app.route('/login')
    def login():
        return render_template('login.html')

    @app.route('/register')
    def register():
        return render_template('register.html')

    @app.route('/map')
    def map():
        if UserService.get_current_user() is None:
            return redirect(url_for('login'))

        return render_template('map.html')

    @app.route('/get_user', methods=['GET'])
    def get_user():
        user = UserService.get_current_user()
        if not (user is None):
            print(user)
            return jsonify({'user': user})
        else:
            return jsonify({'user': None}), 401

    @app.route('/sing_up', methods=['POST'])
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
    def logout():
        UserService.delete_session()
        return redirect(url_for('login'))

    @app.route('/add_marker', methods=['POST'])
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
