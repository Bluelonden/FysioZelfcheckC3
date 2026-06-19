from flask import render_template as rt, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from main import app
from models import db, User, Waardes, Metingen, Triggers, EspDevice, Diagnose
from forms import LoginForm, RegisterForm, WaardesForm, TriggersForm, EspIDForm, UnpairForm
from config import DREMPELWAARDES
from sqlalchemy.exc import IntegrityError
from apis import api
import json

# Registreer de API blueprint
app.register_blueprint(api, url_prefix="/api")
app.config['MAIL_SERVER'] = 'smtp.gmail.com' # Of je provider
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'jouw-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'je-app-wachtwoord' # Let op: gebruik een app-wachtwoord!
mail = Mail(app)


ESP32_IP = "http://192.168.1.50"
@app.route("/", methods=["GET", "POST"])
def home():
    form = EspIDForm()
    unpair_form = UnpairForm() 

    if form.validate_on_submit():
        if current_user.is_authenticated:
            current_user.esp_id = form.esp_id.data
            db.session.commit()
            flash("ESP-ID succesvol gekoppeld!", "success")
        else:
            flash("Log in om uw ESP-ID te koppelen.", "warning")

    return rt("home.html", form=form, unpair_form=unpair_form)

## HOMEPAGE ##
@app.route("/over_ons") 
def over_ons():
    return rt('over_ons.html')

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
    w = user.waardes
    t = user.triggers
    d = user.diagnoses

    context = {}

    if d:
        ziektes = []
        ernst = []
        for item in d:
            ziektes.append(item.ziekte)
            ernst.append(item.ernst)
        # print(ziektes, ernst)

        combi = list(zip(ziektes, ernst))

        context["ziektes"] = combi

    if w:
        context["niveau"] = w.niveau
        context["score"] = w.score
        context["drempels"] = DREMPELWAARDES[w.niveau]
        temp = {
            "leeftijd": w.leeftijd,
            "rookt": w.rookt,
            "symptomen overdag": w.dag,
            "symptomen 's nachts": w.nacht,
            "noodinhalator > 2/week": w.saba,
            "activiteit beperking": w.beperking,
            "ziekenhuisopname de laatste 12 maanden": w.hospital,
            "prednison gebruik de laatste 12 maanden": w.prednison,
            "exacerbaties in de laatste 12 maanden": w.exacerbaties,
        }

        for k, v in temp.items():
            # print(f'DEBUG D DICT K IS {k}\n'
            #       f'DEBUG D DICT V IS {v}')
            if v is True:
                temp[k] = "Ja"
            elif v is False:
                temp[k] = "Nee"
        
        context["waardes"] = temp
    
    if t:
        allergens = t.allergens
        irritants = t.irritants
        pollution = t.pollution

        # print(f'DEBUG ALLERGENS IS {allergens}')
        
        context["triggers"] = {
            "Allergenen": allergens,
            "Irriterende stoffen": irritants,
            "Luchtvervuiling": pollution
        }
        
        # VOOR DEBUG
        # count = 0
        # for label, items in context["triggers"].items():
        #     print(f'DEBUG LABEL: {label}')
        #     for key, value in items.items():   # <-- dict inside list
        #         print(f'KEY: {key}')
        #         print(f'VALUE: {value}')

    return rt("profiel.html", **context)


## SYMPTOMEN VRAGENLIJST ##
@app.route("/vragenlijst", methods=["GET", "POST"])
@login_required
def vragenlijst():
    form = WaardesForm()
    user = current_user
    t = user.triggers

    if form.validate_on_submit():
        waardes = Waardes(
        leeftijd = form.leeftijd.data,
        rookt = form.rookt.data,
        dag = form.dag.data,
        nacht = form.nacht.data,
        saba = form.saba.data,
        beperking = form.beperking.data,
        hospital = form.hospital.data,
        prednison = form.prednison.data,
        exacerbaties = form.exacerbaties.data,
        user_id=user.id
        )

        try:
            
            diagnoses = json.loads(request.form.get("diagnose", "[]"))
            ernst = json.loads(request.form.get("ernst", "{}"))

            for d in diagnoses:
                print(d)
                db.session.add(Diagnose(
                    user_id=current_user.id,
                    ziekte=d,
                    ernst=ernst.get(d)
                ))

            db.session.add(waardes)
            waardes.score_niveau()
            db.session.commit()

            flash("Vragenlijst succesvol opgeslagen!", "success")
            return redirect(url_for('user_ui'))

        except IntegrityError:
            db.session.rollback()
            flash("Deze ESP-ID is al gekoppeld aan een andere gebruiker.", "danger")

        except Exception as e:
            db.session.rollback()
            flash(f"Er is een fout opgetreden: {str(e)}", "danger")

    elif request.method == 'POST':
        print("--- FORMULIER VALIDATIE FOUTEN ---")
        print(form.errors)
        flash("Formulier validatie mislukt. Check de terminal.", "danger")

    return rt('vragenlijst.html', form=form)


## HANDMATIGE TRIGGERS INVOER ##
@app.route('/handmatig', methods=['POST', 'GET'])
@login_required
def handmatig():
    form = TriggersForm()
    user = current_user
    t = user.triggers

    if request.method == 'GET':
        if t:
            flash('Formulier is al eerder ingevuld!', 'danger')
            return redirect(url_for('profiel'))
        return rt('handmatig.html', form=form)

    if form.validate_on_submit():

        allergens = {
            "huisstofmijt": request.form.get("alr_0"),
            "pollen": request.form.get("alr_1"),
            "schimmel": request.form.get("alr_2")
        }

        irritants = {
            "rook": request.form.get("irr_0"),
            "sterke geuren": request.form.get("irr_1"),
            "chemische dampen": request.form.get("irr_2"),
            "schoonmaakmiddelen": request.form.get("irr_3")
        }

        pollution = {
            "smog": request.form.get("pol_0"),
            "uitlaatgassen": request.form.get("pol_1"),
            "fijnstof": request.form.get("pol_2")
        }

        try:
            t = user.triggers

            if t is None:
                t = Triggers(
                    allergens={},
                    irritants={},
                    pollution={},
                    user_id=user.id
                )
                db.session.add(t)
                user.triggers = t

            t.allergens = allergens
            t.irritants = irritants
            t.pollution = pollution

            db.session.commit()

            flash("Gegevens succesvol opgeslagen!", "success")
            return redirect(url_for('profiel'))

        except Exception as e:
            db.session.rollback()
            flash(f"Er is een fout opgetreden: {str(e)}", "danger")

    return rt('handmatig.html', form=form)

## UPDATE VRAGENLIJST ## 
@app.route('/update/vragen', methods=['GET', 'POST'])
@login_required
def update_vragen():
    w = current_user.waardes
    t = current_user.triggers
    form = WaardesForm(obj=w)

    if form.validate_on_submit():

        # update bestaande waardes
        w.leeftijd = form.leeftijd.data
        w.rookt = form.rookt.data
        w.dag = form.dag.data
        w.nacht = form.nacht.data
        w.saba = form.saba.data
        w.beperking = form.beperking.data
        w.hospital = form.hospital.data
        w.prednison = form.prednison.data
        w.exacerbaties = form.exacerbaties.data
        
        diagnoses = json.loads(request.form.get("diagnose", "[]"))
        ernst = json.loads(request.form.get("ernst", "{}"))

        # 1. verwijder bestaande diagnoses van user
        Diagnose.query.filter_by(user_id=current_user.id).delete()
        db.session.flush()

        # 2. insert nieuwe set
        for d in diagnoses:
            print(d)
            db.session.add(Diagnose(
                user_id=current_user.id,
                ziekte=d,
                ernst=ernst.get(d)
            ))

        try:
            v_count = 0
            m_count = 0
            for column in [t.allergens, t.irritants, t.pollution]:
                if column:
                    for value in column.values():
                        if value == "veel":
                            v_count += 1
                        if value == "matig":
                            m_count += 1
                            
            print(f'v_count is {v_count}')
            print(f'm_count is {m_count}')

            db.session.add(w)
            w.score_niveau(v_count, m_count)
            db.session.commit()
            flash("Succesvol opgeslagen!", "success")
            return redirect(url_for("profiel"))

        except Exception as e:
            db.session.rollback()
            flash(f"Fout: {e}", "danger")


    return rt("update_vragen.html", form=form)

## UPDATE HANDMATIGE TRIGGERS ##
@app.route('/update/triggers', methods=['POST', 'GET'])
@login_required
def update_triggers():
    form = TriggersForm()
    t = current_user.triggers
    w = current_user.waardes

    if request.method == 'GET':
        if not t:
            flash("Geen bestaande data gevonden.", "danger")
            return redirect(url_for('handmatig'))
        return rt("update_triggers.html", form=form)

    if not t:
        flash("Je hebt nog geen data om te updaten.", "danger")
        return redirect(url_for('handmatig'))

    if form.validate_on_submit():

        allergens = {
            "huisstofmijt": request.form.get("alr_0"),
            "pollen": request.form.get("alr_1"),
            "schimmel": request.form.get("alr_2")
        }

        irritants = {
            "rook": request.form.get("irr_0"),
            "sterke geuren": request.form.get("irr_1"),
            "chemische dampen": request.form.get("irr_2"),
            "schoonmaakmiddelen": request.form.get("irr_3")
        }

        pollution = {
            "smog": request.form.get("pol_0"),
            "uitlaatgassen": request.form.get("pol_1"),
            "fijnstof": request.form.get("pol_2")
        }

        # print(f'allergens data is: {allergens}')
        # print(f'irritants data is: {irritants}')
        # print(f'pollution data is: {pollution}')

        try:
            t.allergens = allergens
            t.irritants = irritants
            t.pollution = pollution

            v_count = 0
            m_count = 0
            for column in [t.allergens, t.irritants, t.pollution]:
                if column:
                    for value in column.values():
                        if value == "veel":
                            v_count += 1
                        if value == "matig":
                            m_count += 1

            print(f'v_count is {v_count}')
            print(f'm_count is {m_count}')

            db.session.add(w)
            w.score_niveau(v_count, m_count)

            db.session.commit()

            flash("Data succesvol geupdate!", "success")
            return redirect(url_for('profiel'))

        except Exception as e:
            db.session.rollback()
            flash(f"Er is een fout opgetreden: {str(e)}", "danger")

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

    # ESP-ID aanwezig?
    esp_id = data.get("esp_id")
    if not esp_id:
        return jsonify({"error": "esp_id missing"}), 400

    #Zoek ESP
    esp = EspDevice.query.filter_by(esp_id=esp_id).first()

    # Als ESP niet bestaat voeg dit dan toe aan de EspDevice tabel
    if not esp:
        esp = EspDevice(
        esp_id=esp_id,
        esp_secret_hash=generate_password_hash(data.get("esp_password")),
        owner_user_id=None
    )
    db.session.add(esp)
    db.session.commit()


    # Wachtwoordcontrole dit is tegen potentiele spoofing
    esp_pw = data.get("esp_password")
    if not esp_pw or not esp.check_secret(esp_pw):
        return jsonify({"error": "invalid credentials"}), 403

    # Check of ESP gekoppeld is
    if not esp.owner_user_id:
        return jsonify({"error": "esp not claimed"}), 403

    # Meting opslaan
    m = Metingen(
        pm25=data["pm25"],
        pm10=data["pm10"],
        pm1=data["pm1"],
        aqi=data["aqi"],
        co2=data["co2"],
        tvoc=data["tvoc"],
        user_id=esp.owner_user_id
    )

    db.session.add(m)
    db.session.commit()

    return jsonify({"status": "ok"})

@app.route("/user_esp_pairing", methods=['POST'])
@login_required
def user_esp_pairing():
    esp_id = request.form.get("esp_id")
    esp_pw = request.form.get("esp_password")

    if not esp_id or not esp_pw:
        flash("Voer een geldig ESP-ID en wachtwoord in.", "danger")
        return redirect(url_for("home"))

    # Check of ESP_ID al bestaat bij een andere gebruiker
    esp = EspDevice.query.filter_by(esp_id=esp_id).first()

    if not esp:
        flash("Onbekende ESP-ID.", "danger")
        return redirect(url_for("home"))

    if esp.owner_user_id and esp.owner_user_id != current_user.id:
        flash("Deze ESP is al gekoppeld aan een andere gebruiker.", "danger")
        return redirect(url_for("home"))

    # Wachtwoordcontrole
    if not esp.check_secret(esp_pw):
        flash("Wachtwoord onjuist.", "danger")
        return redirect(url_for("home"))

    # Sla ESP_ID op
    esp.owner_user_id = current_user.id
    db.session.commit()

    #Verwijder oude metingen nadat je van ESP_ID switched
    Metingen.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    flash("ESP succesvol gekoppeld!", "success")
    return redirect(url_for("home"))


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

#Dit is de nieuwe unpair route
@app.route("/user_esp_unpair", methods=["POST"])
@login_required
def user_esp_unpair():
    esp = EspDevice.query.filter_by(owner_user_id=current_user.id).first()

    #Unpair de ESP
    if esp:
        esp.owner_user_id = None
        db.session.commit()

        # Verwijder metingen van deze user
        Metingen.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        flash("ESP succesvol ontkoppeld!", "success")

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)