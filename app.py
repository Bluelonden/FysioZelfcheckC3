
from flask import render_template as rt, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from main import app
from forms import LoginForm, RegisterForm, WaardesForm
from models import db, User, Waardes
from config import DREMPELWAARDES
from forms import LoginForm, RegisterForm, Drempelwaardes
import requests
import json

ESP32_IP = "http://192.168.1.50"

@app.route("/")
def home():
    return rt('home.html')

## GET = rt('route.html')
## POST = redirect(url_for('route'))

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'GET':
        if current_user.is_authenticated:
            return rt('dashboard.html')
        else:
            return rt('login.html', form=form)

    if request.method == 'POST':
        username = form.username.data
        password = form.password.data

        if form.validate_on_submit():
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user)
                flash('Welkom terug! Je bent nu ingelogd.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Ongeldige gebruikersnaam of wachtwoord.', 'danger')
                return redirect(url_for('login'))


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if request.method == 'POST':
        username = form.username.data
        email = form.email.data
        password = form.password.data
        role = form.role.data
        waardes = None

        if form.validate_on_submit():
            check_user = User.query.filter_by(username=username).first()
            check_email = User.query.filter_by(email=email).first()

            if check_user:
                flash("Deze gebruikersnaam is al bezet!", "danger")
                return redirect(url_for("register"))

            if check_email:
                flash("Dit e-mailadres is al in gebruik!", "danger")
                return redirect(url_for("register"))

            new_user = User(username=username, email=email, role=role, waardes=waardes)
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            flash("Account succesvol aangemaakt!", "success")
            return redirect(url_for('login'))
    
    return rt('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    return rt('dashboard.html')

@app.route('/results')
@login_required
def results():
    user = current_user
    niveau = user.waardes.niveau
    score = user.waardes.score
    drempels = DREMPELWAARDES[niveau]

    return rt('results.html', niveau=niveau,
              score=score, drempels=drempels)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/vragenlijst", methods=['GET', 'POST'])
# scoring en thresholds
def bereken_score(data):
    score = 0
    # Leeftijd 65+
    try:
        if int(data.get("leeftijd", 0)) >= 65:
            score += 1
    except (TypeError, ValueError):
        pass
    # Roken
    if data.get("rookt"):
        score += 1
    # Symptoomvragen (elke True/Ja = 1)
    symptooms = ["symptoom_dag", "symptoom_nacht", "symptoom_saba", "symptoom_beperking"]
    for s in symptooms:
        if data.get(s):
            score += 1
    # Exacerbaties
    ex = data.get("exacerbaties")
    if ex == "1":
        score += 1
    elif ex == "2+" or ex == "2":
        score += 2
    # Hospitalisatie (afgelopen maanden) -> +1
    if data.get("hospitalisatie"):
        score += 1
    # Prednisongebruik afgelopen 12 maanden -> +2
    if data.get("prednison_gebruik"):
        score += 2
    # Maximaal 8
    return min(score, 8)

def map_score_naar_niveau(score):
    if score <= 2:
        return "Laag"
    if 3 <= score <= 4:
        return "Midden"
    else:
        return "Hoog"

DREMPELWAARDES = {
    "Laag": {
        "PM2.5": {"groen": [0, 10], "oranje": [11, 35], "rood": [36]},
        "PM10": {"groen": [0, 20], "oranje": [21, 50], "rood": [51]},
        "CO2": {"groen": [0, 799], "oranje": [800, 1500], "rood": [1501]},
        "TVOC": {"groen": [0, 299], "oranje": [300, 1000], "rood": [1001]}
    },
    "Midden": {
        "PM2.5": {"groen": [0, 10], "oranje": [11, 25], "rood": [26]},
        "PM10": {"groen": [0, 20], "oranje": [21, 40], "rood": [41]},
        "CO2": {"groen": [0, 699], "oranje": [700, 1200], "rood": [1201]},
        "TVOC": {"groen": [0, 249], "oranje": [250, 800], "rood": [801]}
    },
    "Hoog": {
        "PM2.5": {"groen": [0, 10], "oranje": [11, 20], "rood": [21]},
        "PM10": {"groen": [0, 20], "oranje": [21, 35], "rood": [36]},
        "CO2": {"groen": [0, 599], "oranje": [600, 1000], "rood": [1001]},
        "TVOC": {"groen": [0, 199], "oranje": [200, 600], "rood": [601]}
    }
}

@app.route("/save_thresholds", methods=["POST"])
def save_thresholds():
    thresholds_raw = request.form.get("thresholds")
    thresholds = json.loads(thresholds_raw)

    try:
        r = requests.post(f"{ESP32_IP}/update_thresholds", json=thresholds, timeout=3)
        if r.status_code == 200:
            flash("Drempelwaardes succesvol verzonden naar ESP32!", "success")
        else:
            flash("ESP32 gaf een foutmelding.", "danger")
    except:
        flash("ESP32 niet bereikbaar.", "danger")

    return redirect(url_for("dashboard"))


@app.route("/drempelwaardes", methods=["GET", "POST"])
@login_required
def vragenlijst():
    form = WaardesForm()
    
    if request.method == 'GET':

        if current_user.waardes:
            flash('Formulier is al eerder ingevuld!', 'danger')
            return redirect(url_for('results'))
        else:
            return rt('vragenlijst.html', form=form)

    if request.method == 'POST' and form.validate_on_submit():
        try:    
            leeftijd = form.leeftijd.data
            diagnose = form.diagnose.data
            rookt = form.rookt.data
            dag = form.dag.data
            nacht = form.nacht.data
            saba = form.saba.data
            beperking = form.beperking.data
            hospital = form.hospital.data
            prednison = form.prednison.data
            exacerbaties = form.exacerbaties.data

            data = Waardes(leeftijd=leeftijd, diagnose=diagnose, rookt=rookt,
                            dag=dag, nacht=nacht, saba=saba, beperking=beperking,
                            hospital=hospital, prednison=prednison,
                            exacerbaties=exacerbaties, user=current_user)
            
            data.score_niveau()
            
            db.session.add(data)
            db.session.commit()

            flash("Data succesvol opgeslagen!", "success")
            return redirect(url_for('results'))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Er is een fout opgetreden: {str(e)}", "danger")
    
    return rt("vragenlijst.html", form=form)

if __name__ == "__main__":
    app.run()