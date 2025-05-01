from app import create_app
from flask_jwt_extended import JWTManager
from app.settings import CheckinSettings

app = create_app()
app.config['JWT_SECRET_KEY'] = CheckinSettings.JWT_SECRET
jwt = JWTManager(app)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=('/app/certs/cert.pem','/app/certs/key.pem'))
