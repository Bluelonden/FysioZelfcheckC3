from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from models import Metingen, User
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
    m = Metingen.query.order_by(Metingen.id.desc()).first()

    if m is None:
        return jsonify({
            "values": {
                "pm25": 0,
                "pm10": 0,
                "pm1": 0,
                "aqi": 0,
                "co2": 0,
                "tvoc": 0
            },
            "status": {},
            "groups": {
                "fijnstof": "grey",
                "gassen": "grey"
            },
            "eind": "grey",
            "advies": {
                "binnenbuiten": {"text": "Onbekend", "icon": "house.png", "color": "advies-orange"},
                "sport": {"text": "Onbekend", "icon": "rest.png", "color": "advies-orange"}
            }
        })

    profiel = current_user.waardes.niveau
    data = volledige_status(m, profiel)

    return jsonify(data)

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
    # 1. Haal de patiënt op
    patient = User.query.get_or_404(patient_id)

    # 2. Bepaal profiel
    profiel = "Laag"
    if patient.waardes and patient.waardes.niveau:
        profiel = patient.waardes.niveau

    # 3. Haal de werkelijke metingen op
    metingen = Metingen.query.filter_by(user_id=patient_id)\
                             .order_by(Metingen.timestamp.desc())\
                             .limit(20)\
                             .all()
    
    # Draai de lijst om zodat de oudste eerst komt (voor grafiek weergave)
    metingen.reverse()

    # 4. Data klaarmaken
    labels = [m.timestamp.strftime("%H:%M") for m in metingen] if metingen else []
    
    pm25_data = [m.pm25 for m in metingen]
    pm10_data = [m.pm10 for m in metingen]
    no2_data = [m.no2 for m in metingen] # Aanname: je hebt no2 in je model (zoals in doctor.html gebruikt)
    co2_data = [m.co2 for m in metingen]
    tvoc_data = [m.tvoc for m in metingen]
    aqi_data = [m.aqi for m in metingen]

    # Status berekenen voor de meest recente meting
    status_info = {}
    if metingen:
        latest_m = metingen[-1] # De meest recente na reverse()
        status_data = volledige_status(latest_m, profiel)
        status_info = status_data.get('status', {})

    return jsonify({
        "labels": labels,
        "values": {
            "pm25": pm25_data,
            "pm10": pm10_data,
            "no2": no2_data,
            "co2": co2_data,
            "tvoc": tvoc_data,
            "aqi": aqi_data
        },
        "status": status_info,
        "profiel": profiel
    })


@api.route("/average")
@login_required
def api_average():

    metingen = (
        Metingen.query
        .filter(Metingen.timestamp >= datetime.now() - timedelta(minutes=3))
        .all()
    )

    profiel = current_user.waardes.niveau

    #De fallback heb ik nu in de volledige status functie gebouwt.
    if not metingen:
        return jsonify(volledige_status(None, profiel))

    # gemiddelde berekenen
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
    esp_id = request.args.get("esp_id")

    if not esp_id:
        return jsonify({"error": "esp_id missing"}), 400

    user = User.query.filter_by(esp_id=esp_id).first()

    if not user or not user.waardes:
        return jsonify({"error": "not linked"}), 404

    profiel = user.waardes.niveau
    drempels = DREMPELWAARDES[profiel]

    return jsonify(drempels)