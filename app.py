from flask import render_template as rt, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from main import app
from models import db, User, Waardes, Metingen, Triggers
from forms import LoginForm, RegisterForm, WaardesForm, HandmatigForm, TimeRangeForm
from config import DREMPELWAARDES
import requests
from sqlalchemy.exc import IntegrityError
from apis import api

# Registreer de API blueprint
app.register_blueprint(api, url_prefix="/api")

ESP32_IP = "http://192.168.1.50"

## HOMEPAGE ##
@app.route("/") 
def home():
    return rt('home.html')

## LOGIN ##
@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'GET':
        if current_user.is_authenticated:
            flash('Welkom terug! Je bent nu ingelogd.', 'success')
            if getattr(current_user, 'role', None) == 'arts':
                return redirect(url_for('doctor'))
            return rt('home.html')
        else:
            return rt('login.html', form=form)

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Welkom terug! Je bent nu ingelogd.', 'success')
            
            if getattr(user, 'role', None) == 'arts':
                return redirect(url_for('doctor'))
                
            return redirect(url_for('home'))
        else:
            flash('Ongeldige gebruikersnaam of wachtwoord.', 'danger')
            return redirect(url_for('login'))

## REGISTREREN ##
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('profiel'))
    
    form = RegisterForm()
    
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        role = form.role.data

        try:
            check_user = User.query.filter_by(username=username).first()
            check_email = User.query.filter_by(email=email).first()

            if check_user:
                flash("Deze gebruikersnaam is al bezet!", "danger")
                return redirect(url_for("register"))

            if check_email:
                flash("Dit e-mailadres is al in gebruik!", "danger")
                return redirect(url_for("register"))

            new_user = User(username=username, email=email, password=password, role=role)

            db.session.add(new_user)
            db.session.commit()

            flash("Account succesvol aangemaakt!", "success")
            return redirect(url_for('login'))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Er is een fout opgetreden: {str(e)}", "danger")
    
    return rt('register.html', form=form)

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
        context["niveau"] = waardes.niveau
        context["score"] = waardes.score
        context["drempels"] = DREMPELWAARDES[waardes.niveau]
        context["waardes"] = {
            "leeftijd": waardes.leeftijd,
            "diagnose": waardes.diagnose,
            "ernst": getattr(waardes, 'level', None),
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

## SYMPTOMEN VRAGENLIJST ##
@app.route("/vragenlijst", methods=["GET", "POST"])
@login_required
def vragenlijst():
    form = WaardesForm()

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
            level = getattr(form, 'level', None).data if hasattr(form, 'level') else None
            rookt = form.rookt.data
            dag = form.dag.data
            nacht = form.nacht.data
            saba = form.saba.data
            beperking = form.beperking.data
            hospital = form.hospital.data
            prednison = form.prednison.data
            esp_id = form.esp_id.data
            exacerbaties = int(form.exacerbaties.data)

            # ESP-ID opslaan bij de user
            current_user.esp_id = esp_id

            # Waardes opslaan
            data = Waardes(
                leeftijd=leeftijd,
                diagnose=diagnose,
                level=level,
                rookt=rookt,
                dag=dag,
                nacht=nacht,
                saba=saba,
                beperking=beperking,
                hospital=hospital,
                prednison=prednison,
                exacerbaties=exacerbaties,
                user_id=current_user.id
            )

            data.score_niveau()

            db.session.add(data)
            db.session.commit()  

            flash("Data succesvol opgeslagen!", "success")
            return redirect(url_for('user_ui'))

        except IntegrityError:
            db.session.rollback()
            flash("Deze ESP is al gekoppeld aan een andere gebruiker.", "danger")
            return redirect(url_for('vragenlijst'))

        except Exception as e:
            db.session.rollback()
            flash("Er is een onverwachte fout opgetreden.", "danger")
            return redirect(url_for('vragenlijst'))

    return rt("vragenlijst.html", form=form)


## HANDMATIGE TRIGGERS INVOER ##
@app.route('/handmatig', methods=['POST', 'GET'])
@login_required
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

## UPDATE VRAGENLIJST ## 
## Heb deze 10/06 herschreven zodat hij oude formulierwaardes behoudt ##
@app.route('/update/vragen', methods=['GET', 'POST'])
@login_required
def update_vragen():

    waardes = current_user.waardes
    form = WaardesForm(obj=waardes)

    if request.method == "GET":
        form.esp_id.data = current_user.esp_id

    if form.validate_on_submit():
        form.populate_obj(waardes)
        current_user.esp_id = form.esp_id.data
        waardes.score_niveau()
        

        #Failsave for ESP constraitns
        try:
            db.session.commit()

            flash("Data succesvol geüpdatet!", "success")
            return redirect(url_for('profiel'))

        except IntegrityError:
            db.session.rollback()

            flash(
                "Deze ESP-ID is al gekoppeld aan een andere gebruiker.",
                "danger"
            )

        except Exception as e:
            db.session.rollback()

            flash(
                f"Er is een fout opgetreden: {e}",
                "danger"
            )

    return rt("update_vragen.html", form=form)

## UPDATE HANDMATIGE TRIGGERS ##
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

## ARTSENPORTAL DASHBOARD ##
@app.route("/doctor") 
@login_required
def doctor():
    if getattr(current_user, 'role', None) != 'arts':
        flash("Toegang geweigerd: Deze pagina is exclusief voor artsen.", "danger")
        return redirect(url_for('home'))
    
    pacienten = User.query.filter_by(role='patient').all()
    pacient_id = request.args.get('patient_id', type=int)
    
    geselecteerde_pacient = None
    if pacient_id:
        geselecteerde_pacient = User.query.filter_by(id=pacient_id, role='patient').first()
        
    if not geselecteerde_pacient and pacienten:
        geselecteerde_pacient = pacienten[0]
        
    return rt('doctor.html', 
              pacienten=pacienten, 
              geselecteerde_pacient=geselecteerde_pacient)

## ARTSENPORTAL JSON ENDPOINT ##
@app.route("/api/arts/pacient_data/<int:pacient_id>")
@login_required
def get_pacient_json(pacient_id):
    if getattr(current_user, 'role', None) != 'arts':
        return jsonify({"error": "Niet geautoriseerd"}), 403

    metingen = Metingen.query.filter_by(user_id=pacient_id).order_by(Metingen.timestamp.asc()).all()
    
    timestamps = []
    pm25_waarden = []
    pm10_waarden = []
    no2_waarden = []

    for m in metingen:
        if m.timestamp:
            timestamps.append(m.timestamp.strftime("%Y-%m-%d %H:%M"))
            pm25_waarden.append(m.pm25 if m.pm25 is not None else 0)
            pm10_waarden.append(m.pm10 if m.pm10 is not None else 0)
            
            no2_waarde = getattr(m, 'no2', 0)
            no2_waarden.append(no2_waarde if no2_waarde is not None else 0)

    return jsonify({
        "timestamps": timestamps,
        "pm2.5": pm25_waarden,
        "pm10": pm10_waarden,
        "no2": no2_waarden
    })

## SENSORDATA INKOMEND VANAF ESP32 ##
@app.route("/sensordata", methods=["POST"])
def sensordata():
    data = request.get_json()

    m = Metingen(
        pm25=data["pm25"],
        pm10=data["pm10"],
        pm1=data["pm1"],
        aqi=data["aqi"],
        co2=data["co2"],
        tvoc=data["tvoc"],
        user_id=data.get("user_id", 1)  # test: stuur user_id mee
    )

    db.session.add(m)
    db.session.commit()

    return jsonify({"status": "ok"})

#Paired een user aan esp_id (voor nu nog niet nodig meer voor de toekomst als we een gebruiker het laten aanpassen)
@app.route("/user_esp_pairing", methods=['GET', 'POST']) 
@login_required
def user_esp_pairing():
    if request.method == 'POST':
        esp_id = request.form.get("esp_id")

        if not esp_id:
            flash("Voer een geldig ESP-ID in.", "danger")
            return redirect(url_for("user_esp_pairing"))

        # Sla ESP-ID op bij de user
        current_user.esp_id = esp_id
        db.session.commit()

        flash("ESP-ID succesvol gekoppeld!", "success")
        return redirect(url_for("profiel"))

    return rt("user_ui.html", esp_id=current_user.esp_id)


@app.route("/user_ui", methods=['GET', 'POST'])
@login_required
def user_ui():
    user = current_user

    # 1. User moet eerst de vragenlijst invullen
    if not user.waardes:
        flash("Vul eerst de vragenlijst in om je resultaten en drempelwaardes te bekijken.", "warning")
        return redirect(url_for('vragenlijst'))
    
    #Toon de UI
    niveau = user.waardes.niveau
    score = user.waardes.score
    drempels = DREMPELWAARDES[niveau]

    return rt('user_ui.html',
              niveau=niveau,
              score=score,
              drempels=drempels)




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

