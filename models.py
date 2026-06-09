from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from typing import Optional, List
from flask_login import UserMixin
from flask_migrate import Migrate
from flask_login import LoginManager
from sqlalchemy import String, Integer, Boolean, inspect, ForeignKey as FK
from sqlalchemy.orm import Mapped as Map, mapped_column as mc, relationship as rel
from werkzeug.security import generate_password_hash as gen_hash, check_password_hash as check_hash
import secrets

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id: Map[int] = mc(primary_key=True)
    username: Map[str] = mc(String(150), unique=True, nullable=False)
    email: Map[str] = mc(String(150), unique=True, nullable=False)
    pw_hash: Map[str] = mc(String(256), nullable=False)
    role: Map[str] = mc(String(20), nullable=False)
    status: Map[str] = mc(String(20), nullable=False, default='pending')
    coupling_token: Map[Optional[str]] = mc(String(64), unique=True, nullable=True)
    esp_id: Map[Optional[int]]= mc(unique= True, nullable= True)

    # relationship setup (uselist=False zorgt voor een 1-op-1 relatie)
    waardes: Map[Optional['Waardes']] = rel(back_populates='user', uselist=False)
    triggers: Map[Optional['Triggers']] = rel(back_populates='user', uselist=False)

    def __init__(self, username: str, email: str, password: str, role: str):
        """Maak nieuwe user aan met gehasht password."""
        self.username = username
        self.email = email
        self.pw_hash = gen_hash(password)
        self.role = role

    def set_password(self, password: str):
        """Deze methode wordt gebruikt tijdens registratie/update indien handmatig nodig."""
        self.pw_hash = gen_hash(password)

    def check_password(self, password: str) -> bool:
        """Controle van ingevoerd wachtwoord."""
        return check_hash(self.pw_hash, password)

    def is_coupled(self):
        """Check of gebruiker aan device is gekoppeld."""
        device = Device.query.first()
        if not device:
            return False
        return device.coupled_user_id == self.id

    def generate_coupling_token(self):
        """Genereer een uniek token voor device koppeling."""
        self.coupling_token = secrets.token_hex(32)


class Device(db.Model):
    __tablename__ = 'device'

    id: Map[int] = mc(primary_key=True)
    coupled_user_id: Map[Optional[int]] = mc(FK('user.id'), nullable=True)
    coupled_user: Map[Optional['User']] = rel('User', foreign_keys=[coupled_user_id])

    @staticmethod
    def get():
        """Verkrijg of creëer het device singleton."""
        device = Device.query.first()
        if not device:
            device = Device()
            db.session.add(device)
            db.session.commit()
        return device

    def couple(self, user: 'User'):
        """Koppel een gebruiker aan dit device."""
        if self.coupled_user_id:
            old_user = User.query.get(self.coupled_user_id)
            if old_user:
                old_user.status = 'pending'
                old_user.coupling_token = None

        user.generate_coupling_token()
        user.status = 'approved'
        self.coupled_user_id = user.id


class CoupleRequest(db.Model):
    __tablename__ = 'couple_request'

    id: Map[int] = mc(primary_key=True)
    timestamp: Map[datetime] = mc(db.DateTime, default=datetime.now)
    status: Map[str] = mc(String(20), nullable=False, default='pending')
    user_id: Map[int] = mc(FK('user.id'), nullable=False)
    user: Map['User'] = rel('User', foreign_keys=[user_id])

class Waardes(db.Model):
    __tablename__ = 'waardes'
    
    id: Map[int] = mc(primary_key=True)
    leeftijd: Map[int] = mc(Integer(), nullable=False)
    exacerbaties: Map[int] = mc(Integer(), nullable=False)
    diagnose: Map[str] = mc(String(8), nullable=False)
    level: Map[str] = mc(String(50), nullable=False)
    
    # bool waardes
    rookt: Map[bool] = mc(Boolean, nullable=False)
    dag: Map[bool] = mc(Boolean, nullable=False)
    nacht: Map[bool] = mc(Boolean, nullable=False)
    saba: Map[bool] = mc(Boolean, nullable=False)
    beperking: Map[bool] = mc(Boolean, nullable=False)
    hospital: Map[bool] = mc(Boolean, nullable=False)
    prednison: Map[bool] = mc(Boolean, nullable=False)
    
    score: Map[Optional[int]] = mc(Integer(), default=0)
    niveau: Map[Optional[str]] = mc(String(6))
    # foreign key setup
    user_id: Map[int] = mc(FK('user.id'), unique=True, nullable=False)

    # relationship setup
    user: Map['User'] = rel(back_populates='waardes')
    
    def __init__(self, leeftijd: int, diagnose: str, level: str, rookt: bool, 
                 dag: bool, nacht: bool, saba: bool, beperking: bool, 
                 hospital: bool, prednison: bool, exacerbaties: int, user_id: int):
            
            self.leeftijd = leeftijd
            self.diagnose = diagnose
            self.level = level
            self.rookt = rookt
            self.dag = dag
            self.nacht = nacht
            self.saba = saba
            self.beperking = beperking
            self.hospital = hospital
            self.prednison = prednison
            self.exacerbaties = exacerbaties
            self.user_id = user_id

    def bereken_score(self):
        score = 0
        try:
            if self.leeftijd >= 65:
                score += 1
        except (TypeError, ValueError):
            pass
        if self.rookt:
            score += 1
        # Symptoomvragen (elke True/Ja = +1)
        symptooms = [self.dag, self.nacht, self.saba, self.beperking]
        for s in symptooms:
            if s:
                score += 1
        ex = self.exacerbaties
        if ex == 1:
            score += 1
        elif ex == 2:
            score += 2
        if self.hospital:
            score += 1
        if self.prednison:
            score += 2
        return min(score, 8)
    
    def score_niveau(self):
        self.score = self.bereken_score()
        score = self.score
        if score <= 2:
            self.niveau = "Laag"
        elif 3 <= score <= 4:
            self.niveau = "Midden"
        else:
            self.niveau = "Hoog"


class Triggers(db.Model):
    __tablename__ = 'triggers'

    id: Map[int] = mc(primary_key=True)
    allergens: Map[str] = mc(String(10), nullable=False)
    irritants: Map[str] = mc(String(10), nullable=False)
    infection: Map[str] = mc(String(10), nullable=False)
    exercise: Map[str] = mc(String(10), nullable=False)
    weather: Map[str] = mc(String(10), nullable=False)
    pollution: Map[str] = mc(String(10), nullable=False)
    user_id: Map[int] = mc(FK('user.id'), unique=True, nullable=False)

    user: Map['User'] = rel(back_populates='triggers')

    def __init__(self, allergens: str, irritants: str, infection: str, 
                 exercise: str, weather: str, pollution: str, user_id: int):
        self.allergens = allergens
        self.irritants = irritants
        self.infection = infection
        self.exercise = exercise
        self.weather = weather
        self.pollution = pollution
        self.user_id = user_id


def exists():
    """Check if database tables exist."""
    engine = db.engine
    inspector = inspect(engine)
    table = inspector.get_table_names()
    return len(table) > 0
class Metingen(db.Model):
    __tablename__ = "measurement"

    id: Map[int] = mc(primary_key=True)
    pm25: Map[float] = mc(db.Float, nullable=False)
    pm10: Map[float] = mc(db.Float, nullable=False)
    pm1: Map[float] = mc(db.Float, nullable=False)
    aqi: Map[float] = mc(db.Float, nullable=False)
    co2: Map[float] = mc(db.Float, nullable=False)
    tvoc: Map[float] = mc(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)

    user_id: Map[int] = mc(FK("user.id"), nullable=True)
    user: Map["User"] = rel(backref="measurements")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
