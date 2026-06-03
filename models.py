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

    # 'pending' | 'approved' | 'denied'
    status: Map[str] = mc(String(20), nullable=False, default='pending')

    # Gegenereerd op het moment dat een arts de koppeling goedkeurt
    coupling_token: Map[Optional[str]] = mc(String(64), unique=True, nullable=True)

    waardes: Map[Optional['Waardes']] = rel(back_populates='user', uselist=False)

    def set_password(self, password):
        self.pw_hash = gen_hash(password)

    def check_password(self, password):
        return check_hash(self.pw_hash, password)

    def is_coupled(self):
        device = Device.query.first()
        if not device:
            return False
        return device.coupled_user_id == self.id

    def generate_coupling_token(self):
        self.coupling_token = secrets.token_hex(32)


class Device(db.Model):
    __tablename__ = 'device'

    id: Map[int] = mc(primary_key=True)

    # De enige rij in deze tabel — één device, één actieve koppeling
    coupled_user_id: Map[Optional[int]] = mc(FK('user.id'), nullable=True)
    coupled_user: Map[Optional['User']] = rel('User', foreign_keys=[coupled_user_id])

    @staticmethod
    def get():
        device = Device.query.first()
        if not device:
            device = Device()
            db.session.add(device)
            db.session.commit()
        return device

    def couple(self, user: 'User'):
        # Ontkoppel de huidige gebruiker als die er is
        if self.coupled_user_id:
            old_user = User.query.get(self.coupled_user_id)
            if old_user:
                old_user.status = 'pending'
                old_user.coupling_token = None

        # Genereer een nieuw token en koppel de nieuwe gebruiker
        user.generate_coupling_token()
        user.status = 'approved'
        self.coupled_user_id = user.id


class CoupleRequest(db.Model):
    __tablename__ = 'couple_request'

    id: Map[int] = mc(primary_key=True)
    timestamp: Map[datetime] = mc(db.DateTime, default=datetime.now)

    # 'pending' | 'approved' | 'denied'
    status: Map[str] = mc(String(20), nullable=False, default='pending')

    user_id: Map[int] = mc(FK('user.id'), nullable=False)
    user: Map['User'] = rel('User', foreign_keys=[user_id])


class Waardes(db.Model):
    __tablename__ = 'waardes'

    id: Map[int] = mc(primary_key=True)
    leeftijd: Map[int] = mc(Integer(), nullable=False)
    diagnose: Map[str] = mc(String(8), nullable=False)
    rookt: Map[bool] = mc(Boolean, nullable=False)
    dag: Map[bool] = mc(Boolean, nullable=False)
    nacht: Map[bool] = mc(Boolean, nullable=False)
    saba: Map[bool] = mc(Boolean, nullable=False)
    beperking: Map[bool] = mc(Boolean, nullable=False)
    hospital: Map[bool] = mc(Boolean, nullable=False)
    prednison: Map[bool] = mc(Boolean, nullable=False)
    exacerbaties: Map[int] = mc(Integer(), nullable=False)
    score: Map[Optional[int]] = mc(Integer(), default=0)
    niveau: Map[Optional[str]] = mc(String(6))

    user_id: Map[int] = mc(FK('user.id'), unique=True, nullable=False)
    user: Map['User'] = rel(back_populates='waardes')

    def bereken_score(self):
        score = 0
        try:
            if self.leeftijd >= 65:
                score += 1
        except (TypeError, ValueError):
            pass
        if self.rookt:
            score += 1
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


def exists():
    engine = db.engine
    inspector = inspect(engine)
    table = inspector.get_table_names()
    return len(table) > 0


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
