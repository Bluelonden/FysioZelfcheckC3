from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_migrate import Migrate
from flask_login import LoginManager
from sqlalchemy import String, inspect
from sqlalchemy.orm import Mapped as Map, mapped_column as mc
from werkzeug.security import generate_password_hash, check_password_hash # belangrijk voor hashing

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

class User(db.Model, UserMixin):
    # updated model setup
    id: Map[int] = mc(primary_key=True)
    username: Map[str] = mc(String(150), unique=True, nullable=False)
    email: Map[str] = mc(String(150), unique=True, nullable=False)
    password_hash: Map[str] = mc(String(256), nullable=False)
    role: Map[str] = mc(String(20), nullable=False)

    # id = db.Column(db.Integer, primary_key=True)
    # username = db.Column(db.String(150), unique=True, nullable=False)
    # email = db.Column(db.String(150), unique=True, nullable=False)
    # password_hash = db.Column(db.String(256), nullable=False)  # dit is de password_hash
    # role = db.Column(db.String(20), nullable=False)

    # deze methode wordt gebruikt tijdens registratie
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # deze methode wordt gebruikt tijdens login
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def exists():
    engine = db.engine
    inspector = inspect(engine)
    table = inspector.get_table_names()

    return len(table) > 0

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))