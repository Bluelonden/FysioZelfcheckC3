from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager
from sqlalchemy.orm import Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id: int):
    return db.session.get(User, int(user_id))

class User(db.Model, UserMixin):
    """
    De User-klasse representeert zowel de database-tabel als het 
    gebruikersobject voor authenticatie.
    """
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    
    def check_password(self, password: str) -> bool:
        """Controleert of een ingevoerd wachtwoord overeenkomt met de opgeslagen hash."""
        return check_password_hash(self.password_hash, password)