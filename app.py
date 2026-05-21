from flask import render_template as rt, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from main import app
from models import db, User, Waardes, Metingen
from forms import LoginForm, RegisterForm, WaardesForm
from config import DREMPELWAARDES
import requests
from apis import api
app.register_blueprint(api, url_prefix="/api")



ESP32_IP = "http://192.168.1.50"

@app.route("/") #Dit is de homepage 
def home():
    return rt('home.html')

@app.route("/login", methods=['GET', 'POST']) #Login route
def login():
    form = LoginForm()

    if request.method == 'GET':
        if current_user.is_authenticated:
            flash('Welkom terug! Je bent nu ingelogd.', 'success')
            return rt('home.html')
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
                return redirect(url_for('home'))
            else:
                flash('Ongeldige gebruikersnaam of wachtwoord.', 'danger')
                return redirect(url_for('login'))


@app.route("/register", methods=['GET', 'POST']) #Register route
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

@app.route('/results')
@login_required
def results():
    user = current_user
    
    if user.waardes is None: #Als de gebruier nog geen Drempelwaardesprofiel heeft return dan niks
        return rt('results.html', niveau=None, score=None, drempels=None)
    
    niveau = user.waardes.niveau
    score = user.waardes.score
    drempels = DREMPELWAARDES[niveau]
    m = Metingen.query.order_by(Metingen.id.desc()).first()

    return rt(
        'results.html',
        niveau=niveau,
        score=score,
        drempels=drempels,

    )


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


#Dit is om de drempelwaardes naar de ESP te posten
@app.route("/save_thresholds", methods=["POST"])
def save_thresholds():
    thresholds = request.get_json()

    #Kijkt of je verbinding hebt met de ESP en zo ja post de Drempelwaardes
    r = requests.post(f"{ESP32_IP}/update_thresholds", json=thresholds, timeout=3)
    if r.status_code == 200:
            flash("Drempelwaardes succesvol verzonden naar ESP32!", "success")
    else:
            flash("ESP32 gaf een foutmelding.", "danger")

    return redirect(url_for("results"))


@app.route("/vragenlijst", methods=["GET", "POST"])
@login_required
def vragenlijst():
    form = WaardesForm()

    if form.validate_on_submit():
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

@app.route("/sensordata", methods=["POST"]) 
def sensordata():
    data = request.get_json()

    m = Metingen(
        pm25=data["pm25"],
        pm10=data["pm10"],
        pm1=data["pm1"],
        aqi=data["aqi"],
        co2=data["co2"],
        tvoc=data["tvoc"]
    )

    db.session.add(m)
    db.session.commit()

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000,debug=True)