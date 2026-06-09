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
    patient = User.query.get_or_404(patient_id)

    profiel = "Laag"
    if patient.waardes and patient.waardes.niveau:
        profiel = patient.waardes.niveau

    drempels = DREMPELWAARDES.get(profiel, DREMPELWAARDES["Laag"])

    pm25_rood_grens = drempels["PM25"]["oranje_max"]
    pm10_rood_grens = drempels["PM10"]["oranje_max"]

    pm25_data = [round(random.uniform(2, pm25_rood_grens + 8), 1) for _ in range(7)]
    pm10_data = [round(random.uniform(5, pm10_rood_grens + 15), 1) for _ in range(7)]
    no2_data = [round(random.uniform(10.0, 45.0), 1) for _ in range(7)]

    labels = []
    nu = datetime.now()
    for i in range(6, -1, -1):
        labels.append((nu - timedelta(hours=i)).strftime("%H:%M"))

    return jsonify({
        "labels": labels,
        "values": {
            "pm25": pm25_data,
            "pm10": pm10_data,
            "no2": no2_data
        },
        "profiel": profiel
    })


@api.route("/average")
@login_required
def api_average():

    metingen = (
        Metingen.query
        .filter(Metingen.timestamp >= datetime.now() - timedelta(minutes=5)) #Je wilt het gemiddelde van de afgelopen 5 minuten
        .all()
    )

    if not metingen:
        return jsonify({})  # of een fallback

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

    profiel = current_user.waardes.niveau
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


