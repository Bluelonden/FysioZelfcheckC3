from flask import render_template as rt, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from main import app
from models import db, User, Waardes, Metingen, Triggers
from forms import LoginForm, RegisterForm, WaardesForm, HandmatigForm
from config import DREMPELWAARDES
import requests
from apis import api
app.register_blueprint(api, url_prefix="/api")



ESP32_IP = "http://192.168.1.50"

## HOMEPAGE ##
@app.route("/") #Dit is de homepage
def home():
    return rt('home.html')

## LOGIN ##
@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'GET':
        if current_user.is_authenticated:
            flash('Welkom terug! Je bent nu ingelogd.', 'success')
            return rt('home.html')
        else:
            return rt('login.html', form=form)


    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        # check wachtwoord
        if user and user.check_password(password):
            login_user(user)
            flash('Welkom terug! Je bent nu ingelogd.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Ongeldige gebruikersnaam of wachtwoord.', 'danger')
            return redirect(url_for('login'))

## REGISTREREN ##
@app.route("/register", methods=['GET', 'POST'])
def register():

    # al ingelogd = naar profiel
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    
    form = RegisterForm()
    
    if form.validate_on_submit():
        try:
            username = form.username.data
            email = form.email.data
            password = form.password.data
            role = form.role.data

            new_user = User(username=username, email=email,
                            password=password, role=role)

            # opslaan in database
            db.session.add(new_user)
            db.session.commit()

            flash("Account succesvol aangemaakt!", "success")
            return redirect(url_for('login'))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Er is een fout opgetreden: {str(e)}", "danger")
    
    return rt('register.html', form=form)

## RESULTATEN WEERGEVEN ##
@app.route('/results')
@login_required
def results():
    user = current_user

    # CONTROLE: Heeft de gebruiker de vragenlijst al ingevuld?
    if not user.waardes:
        flash("Vul eerst de vragenlijst in om je resultaten en drempelwaardes te bekijken.", "warning")
        return redirect(url_for('vragenlijst'))

    niveau = user.waardes.niveau
    score = user.waardes.score
    drempels = DREMPELWAARDES[niveau]
    m = Metingen.query.order_by(Metingen.id.desc()).first()

    try:
        requests.post(f"{ESP32_IP}/update_thresholds", json=drempels, timeout=3)
        flash("Drempelwaardes automatisch verzonden naar ESP32!", "success")
    except requests.exceptions.RequestException:
        flash("Kon geen verbinding maken met de ESP32.", "danger")

    return rt('results.html', niveau=niveau, score=score, drempels=drempels)

## LOGOUT ##
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

## USER PROFIEL ##
@app.route('/profiel')
@login_required
def profiel():
    user = current_user
    waardes = user.waardes
    triggers = user.triggers
    context = {}

    if waardes:
        # context["niveau"] = user.waardes.niveau
        # context["score"] = user.waardes.score
        # context["drempels"] = DREMPELWAARDES[user.waardes.niveau]
        context["niveau"] = waardes.niveau
        context["score"] = waardes.score
        context["waardes"] = {
            "leeftijd": waardes.leeftijd,
            "diagnose": waardes.diagnose,
            "ernst": waardes.level,
            "rookt": waardes.rookt,
            "symptomen overdag": waardes.dag,
            "symptomen 's nachts": waardes.nacht,
            "noodinhalator": waardes.saba,
            "activiteit beperking": waardes.beperking,
            "ziekenhuisopname afgelopen 12 maanden": waardes.hospital,
            "prednison gebruik afgelopen 12 maanden": waardes.prednison,
            "exacerbaties in afgelopen 12 maanden": waardes.exacerbaties,
        }

    if triggers:
        context["triggers"] = {
            "allergenen": triggers.allergens,
            "irriterende stoffen": triggers.irritants,
            "luchtweginfecties": triggers.infection,
            "sporten": triggers.exercise,
            "weer": triggers.weather,
            "luchtvervuiling": triggers.pollution,
        }

    return rt("profiel.html", **context)

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

## SYMPTOMEN VRAGENLIJST ##
@app.route("/vragenlijst", methods=["GET", "POST"])
@login_required
def vragenlijst():
    form = WaardesForm()

    # check if user has already filled in the form
    if request.method == 'GET':
        if current_user.waardes:
            flash('Formulier is al eerder ingevuld!', 'danger')
            return redirect(url_for('profiel'))
        else:
            return rt('vragenlijst.html', form=form)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            leeftijd = form.leeftijd.data
            diagnose = form.diagnose.data
            level = form.level.data
            rookt = form.rookt.data
            dag = form.dag.data
            nacht = form.nacht.data
            saba = form.saba.data
            beperking = form.beperking.data
            hospital = form.hospital.data
            prednison = form.prednison.data
            exacerbaties = int(form.exacerbaties.data) #integer aan toegevoegd voor zekerheid (coercion error wtf-forms)

            data = Waardes(leeftijd=leeftijd, diagnose=diagnose, level=level,
                            rookt=rookt, dag=dag, nacht=nacht, saba=saba,
                            beperking=beperking, hospital=hospital,
                            prednison=prednison, exacerbaties=exacerbaties,
                            user_id=current_user.id)

            data.score_niveau()

            db.session.add(data)
            db.session.commit()

            flash("Data succesvol opgeslagen!", "success")
            return redirect(url_for('results'))

        except Exception as e:
            db.session.rollback()
            flash(f"Er is een fout opgetreden: {str(e)}", "danger")

    return rt("vragenlijst.html", form=form)

@app.route('/handmatig', methods=['POST', 'GET'])
def handmatig():
    form = HandmatigForm()
    user = current_user
    
    if request.method == 'GET':
        if current_user.triggers:
            flash('Formulier is al eerder ingevuld!', 'danger')
            return redirect(url_for('profiel'))
        else:
            return rt('handmatig.html', form=form)
    
    if form.validate_on_submit():
        try:
            allergens = form.allergens.data
            irritants = form.irritants.data
            infection = form.infection.data
            exercise = form.exercise.data
            weather = form.weather.data
            pollution = form.pollution.data

            triggers = Triggers(allergens=allergens, irritants=irritants,
                                infection=infection, exercise=exercise,
                                weather=weather, pollution=pollution,
                                user_id=user.id)
            
            db.session.add(triggers)
            db.session.commit()

            flash("Gegevens succesvol opgeslagen!", "success")
            return redirect(url_for('profiel'))

        except Exception as e:
            db.session.rollback()
            flash(f"Er is een fout opgetreden: {str(e)}", "danger")
            
    return rt('handmatig.html', form=form)

@app.route('/update/vragen', methods=['POST', 'GET'])
@login_required
def update_vragen():
    form = WaardesForm(obj=current_user)
    waardes = current_user.waardes

    if request.method == 'POST' and form.validate_on_submit():
        waardes.leeftijd = form.leeftijd.data
        waardes.diagnose = form.diagnose.data
        waardes.level = form.level.data
        waardes.rookt = form.rookt.data
        waardes.dag = form.dag.data
        waardes.nacht = form.nacht.data
        waardes.saba = form.saba.data
        waardes.beperking = form.beperking.data
        waardes.hospital = form.hospital.data
        waardes.prednison = form.prednison.data
        waardes.exacerbaties = form.exacerbaties.data

        waardes.score_niveau()

        try:
            db.session.commit()

            flash("Data succesvol geupdate!", "success")
            return redirect(url_for('profiel'))

        except Exception as e:
            db.session.rollback()
            flash(f"Er is een fout opgetreden: {str(e)}", "danger")
            return rt('update_vragen.html', form=form)

    return rt("update_vragen.html", form=form)

@app.route('/update/triggers', methods=['POST', 'GET'])
@login_required
def update_triggers():
    form = HandmatigForm(obj=current_user)
    triggers = current_user.triggers

    if request.method == 'POST' and form.validate_on_submit():
        triggers.allergens = form.allergens.data
        triggers.irritants = form.irritants.data
        triggers.infection = form.infection.data
        triggers.exercise = form.exercise.data
        triggers.weather = form.weather.data
        triggers.pollution = form.pollution.data

        try:
            db.session.commit()

            flash("Data succesvol geupdate!", "success")
            return redirect(url_for('profiel'))

        except Exception as e:
            db.session.rollback()
            flash(f"Er is een fout opgetreden: {str(e)}", "danger")
            return rt('update_triggers.html', form=form)

    return rt("update_triggers.html", form=form)


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
    app.run(host="0.0.0.0", port=5000, debug=True)