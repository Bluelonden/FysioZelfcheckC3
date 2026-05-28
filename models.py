from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from typing import Optional, List
from flask_login import UserMixin
from flask_migrate import Migrate
from flask_login import LoginManager
from sqlalchemy import String, Integer, Boolean, inspect, ForeignKey as FK
from sqlalchemy.orm import Mapped as Map, mapped_column as mc, relationship as rel
from werkzeug.security import generate_password_hash as gen_hash, check_password_hash as check_hash 

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    # int waardes
    id: Map[int] = mc(primary_key=True)

    # str waardes
    username: Map[str] = mc(String(150), unique=True, nullable=False)
    email: Map[str] = mc(String(150), unique=True, nullable=False)
    pw_hash: Map[str] = mc(String(256), nullable=False)
    role: Map[str] = mc(String(20), nullable=False)

    # optionele waardes
    waardes: Map[Optional['Waardes']] = rel(back_populates='user', uselist=False)

    # deze methode wordt gebruikt tijdens registratie
    def set_password(self, password):
        self.pw_hash = gen_hash(password)

    # deze methode wordt gebruikt tijdens login
    def check_password(self, password):
        return check_hash(self.pw_hash, password)

class Waardes(db.Model):
    __tablename__ = 'waardes'
    
    # int waardes
    id: Map[int] = mc(primary_key=True)
    leeftijd: Map[int] = mc(Integer(), nullable=False)
   
    # str waardes
    diagnose: Map[str] = mc(String(8), nullable=False)
    
    # bool waardes
    rookt: Map[bool] = mc(Boolean, nullable=False)
    dag: Map[bool] = mc(Boolean, nullable=False)
    nacht: Map[bool] = mc(Boolean, nullable=False)
    saba: Map[bool] = mc(Boolean, nullable=False)
    beperking: Map[bool] = mc(Boolean, nullable=False)
    hospital: Map[bool] = mc(Boolean, nullable=False)
    prednison: Map[bool] = mc(Boolean, nullable=False)
    exacerbaties: Map[int] = mc(Integer(), nullable=False)
    
    # optionele waardes
    score: Map[Optional[int]] = mc(Integer(), default=0)
    niveau: Map[Optional[str]] = mc(String(6))

    # foreign key setup
    user_id: Map[int] = mc(FK('user.id'), unique=True, nullable=False)
    user: Map['User'] = rel(back_populates='waardes')
    
    def bereken_score(self):
        score = 0
        # Leeftijd 65+
        try:
            if self.leeftijd >= 65:
                score += 1
        except (TypeError, ValueError):
            pass
        # Roken
        if self.rookt:
            score += 1
        # Symptoomvragen (elke True/Ja = 1)
        symptooms = [self.dag, self.nacht, self.saba, self.beperking]
        for s in symptooms:
            if s:
                score += 1
        # Exacerbaties
        ex = self.exacerbaties
        if ex == 1:
            score += 1
        elif ex == 2:
            score += 2
        # Hospitalisatie (afgelopen maanden) -> +1
        if self.hospital:
            score += 1
        # Prednisongebruik afgelopen 12 maanden -> +2
        if self.prednison:
            score += 2
        # Maximaal 8
        print(f'this user\'s score is: {min(score, 8)}')
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

def exists():
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
    timestamp = db.Column(db.DateTime, default=datetime.now) #Haal de tijd uit de device die de server host

    user_id: Map[int] = mc(FK("user.id"), nullable=True)
    user: Map["User"] = rel(backref="measurements")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


