
from flask import render_template as rt, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from main import app
from forms import LoginForm, RegisterForm,Drempelwaardes
from models import db, User

@app.route("/")
def home():
    return rt('home.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'GET' and current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if form.validate_on_submit():
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user)
                flash('Welkom terug! Je bent nu ingelogd.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Ongeldige gebruikersnaam of wachtwoord.', 'danger')
                return redirect(url_for('login'))

    return rt('login.html', form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if request.method == 'GET':
        return rt("register.html", form=form)

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        if form.validate_on_submit():
            check_user = User.query.filter_by(username=username).first()
            check_email = User.query.filter_by(email=email).first()

            if check_user:
                flash("Deze gebruikersnaam is al bezet!", "danger")
                return redirect(url_for("register"))

            if check_email:
                flash("Dit e-mailadres is al in gebruik!", "danger")
                return redirect(url_for("register"))

            new_user = User(username=username, email=email, role=role)
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            flash("Account succesvol aangemaakt!", "success")
            return redirect(url_for('login'))

    return rt("register.html", form=form)


@app.route("/dashboard")
@login_required
def dashboard():
    return rt("dashboard.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/gegevens")
def metingen():
    return rt("home.html")

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

def map_score_naar_niveau(score: int) -> str:
    if score <= 2:
        return "Laag"
    if 3 <= score <= 4:
        return "Midden"
    return "Hoog"

DREMPELWAARDES = {
    "Laag": {
        "PM2.5": {"groen": (0,10), "oranje": (11,35), "rood": (36,)},
        "PM10": {"groen": (0,20), "oranje": (21,50), "rood": (51,)},
        "CO2": {"groen": (0,799), "oranje": (800,1500), "rood": (1501,)},
        "TVOC": {"groen": (0,299), "oranje": (300,1000), "rood": (1001,)}
    },
    "Midden": {
        "PM2.5": {"groen": (0,10), "oranje": (11,25), "rood": (26,)},
        "PM10": {"groen": (0,20), "oranje": (21,40), "rood": (41,)},
        "CO2": {"groen": (0,699), "oranje": (700,1200), "rood": (1201,)},
        "TVOC": {"groen": (0,249), "oranje": (250,800), "rood": (801,)}
    },
    "Hoog": {
        "PM2.5": {"groen": (0,10), "oranje": (11,20), "rood": (21,)},
        "PM10": {"groen": (0,20), "oranje": (21,35), "rood": (36,)},
        "CO2": {"groen": (0,599), "oranje": (600,1000), "rood": (1001,)},
        "TVOC": {"groen": (0,199), "oranje": (200,600), "rood": (601,)}
    }
}


@app.route("/drempelwaardes", methods=["GET", "POST"])
@login_required
def drempelwaardes_route():
    form = Drempelwaardes()

    if form.validate_on_submit():
        # Bouw een eenvoudige dict met de formwaarden
        data = {
            "leeftijd": form.leeftijd.data,
            "diagnose": form.diagnose.data if hasattr(form, "diagnose") else None,
            "rookt": bool(form.rookt.data),
            "symptoom_dag": bool(getattr(form, "symptoom_dag").data),
            "symptoom_nacht": bool(getattr(form, "symptoom_nacht").data),
            "symptoom_saba": bool(getattr(form, "symptoom_saba").data),
            "symptoom_beperking": bool(getattr(form, "symptoom_beperking").data),
            "exacerbaties": form.exacerbaties.data if hasattr(form, "exacerbaties") else "0",
            "hospitalisatie": bool(getattr(form, "hospitalisatie").data) if hasattr(form, "hospitalisatie") else False,
            "prednison_hosp": bool(getattr(form, "prednison_hosp").data) if hasattr(form, "prednison_hosp") else False
        }

        score = bereken_score(data)
        niveau = map_score_naar_niveau(score)
        drempels = DREMPELWAARDES[niveau]

        return rt("drempels_result.html", score=score, niveau=niveau, drempels=drempels, data=data)
    
    return rt("drempels_form.html", form=form)

