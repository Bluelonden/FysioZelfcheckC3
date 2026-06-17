from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from models import Metingen, User, EspDevice
from statuscalc import bereken_status, volledige_status
from datetime import datetime, timedelta
import random
from config import DREMPELWAARDES

api = Blueprint("api", __name__)

def livedata_grafiek(column):
    minutes = request.args.get("minutes", default=1, type=int)
    minutes = max(1, min(minutes, 1440))
    
    laatste_uur = datetime.now() - timedelta(minutes=minutes)
    metingen = (
    Metingen.query
    .filter_by(user_id=current_user.id)
    .filter(Metingen.timestamp >= laatste_uur)
    .order_by(Metingen.timestamp.asc())
    .all()
    )


    labels = [m.timestamp.strftime("%H:%M") for m in metingen]
    values = [getattr(m, column) for m in metingen]

    return jsonify({
        "labels": labels,
        "values": values
    })


@api.route("/latest")
@login_required
def api_latest():
    #Veiligheidscheck
    if not current_user.waardes:
        return jsonify({"error": "User has no waardes profile"}), 400

    #Huidige waardes
    profiel = current_user.waardes.niveau

    # Haal alle metingen op van deze gebruiker
    metingen = (
        Metingen.query
        .filter_by(user_id=current_user.id)
        .order_by(Metingen.timestamp.desc())
        .all()
    )

    #Als er geen metingen zijn stuur dan een lege status terug
    if not metingen:
        return jsonify(volledige_status(None, profiel))

    # Laatste meting
    m = metingen[0]

    return jsonify(volledige_status(m, profiel))

@api.route("/pm25_fig")
def pm25_fig():
    return livedata_grafiek("pm25")

@api.route("/pm10_fig")
def pm10_fig():
    return livedata_grafiek("pm10")

@api.route("/pm1_fig")
def pm1_fig():
    return livedata_grafiek("pm1")

@api.route("/aqi_fig")
def aqi_fig():
    return livedata_grafiek("aqi")

@api.route("/co2_fig")
def co2_fig():
    return livedata_grafiek("co2")

@api.route("/tvoc_fig")
def tvoc_fig():
    return livedata_grafiek("tvoc")


@api.route('/arts/pacient_data/<int:patient_id>')
@login_required
def arts_pacient_data(patient_id):
    patient = User.query.get_or_404(patient_id)
    profiel = patient.waardes.niveau if patient.waardes else "Laag"

    # Metingen ophalen (zoals je al had)
    metingen = Metingen.query.filter_by(user_id=patient_id)\
                             .order_by(Metingen.timestamp.desc())\
                             .limit(20)\
                             .all()
    metingen.reverse()

    labels = [m.timestamp.strftime("%H:%M") for m in metingen] if metingen else []
    
    # Let op: zorg dat 'no2' in je Metingen model staat!
    return jsonify({
        "labels": labels,
        "values": {
            "pm25": [m.pm25 for m in metingen],
            "pm10": [m.pm10 for m in metingen],
            "no2": [getattr(m, 'no2', 0) for m in metingen], 
            "co2": [m.co2 for m in metingen],
            "tvoc": [m.tvoc for m in metingen],
            "aqi": [m.aqi for m in metingen]
        },
        # HIER IS DE FIX:
        "status": volledige_status(metingen[-1], profiel).get('status', {}) if metingen else {},
        "groups": volledige_status(metingen[-1], profiel).get('groups', {}) if metingen else {},
        "profiel": profiel
    })

@api.route("/average")
@login_required
def api_average():

    # Veiligheidscheck
    if not current_user.waardes:
        return jsonify({"error": "User has no waardes profile"}), 400

    #Added user filtering
    metingen = (
        Metingen.query
        .filter_by(user_id=current_user.id)
        .filter(Metingen.timestamp >= datetime.now() - timedelta(minutes=3))
        .all()
    )

    profiel = current_user.waardes.niveau

    if not metingen:
        return jsonify(volledige_status(None, profiel))

    avg = {
        "pm1": sum(m.pm1 for m in metingen) / len(metingen),
        "pm25": sum(m.pm25 for m in metingen) / len(metingen),
        "pm10": sum(m.pm10 for m in metingen) / len(metingen),
        "co2": sum(m.co2 for m in metingen) / len(metingen),
        "tvoc": sum(m.tvoc for m in metingen) / len(metingen),
        "aqi": sum(m.aqi for m in metingen) / len(metingen),
    }

    class Fake: pass
    f = Fake()
    f.pm1 = avg["pm1"]
    f.pm25 = avg["pm25"]
    f.pm10 = avg["pm10"]
    f.co2 = avg["co2"]
    f.tvoc = avg["tvoc"]
    f.aqi = avg["aqi"]

    data = volledige_status(f, profiel)

    return jsonify(data)


@api.route("/esp/get_thresholds")
def esp_get_thresholds():
    esp_id = request.args.get("esp_id", type=int)

    if not esp_id:
        return jsonify({"error": "esp_id missing"}), 400

    esp = EspDevice.query.filter_by(esp_id=esp_id).first()
    if not esp or not esp.owner_user_id:
        return jsonify({"error": "device not linked to a user"}), 404

    user = User.query.get(esp.owner_user_id)
    if not user or not user.waardes:
        return jsonify({"error": "user profile missing"}), 404

    profiel = user.waardes.niveau
    drempels = DREMPELWAARDES.get(profiel)
    if not drempels:
        return jsonify({"error": "configured profile name invalid"}), 500

    return jsonify(drempels)

