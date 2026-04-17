from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_migrate import Migrate
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash # belangrijk voor hashing

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)  # dit is de password_hash

    # deze methode wordt gebruikt tijdens registratie
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # deze methode wordt gebruikt tijdens login
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))