from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from models import Metingen, User
from statuscalc import bereken_status
from datetime import datetime, timedelta
import random
from config import DREMPELWAARDES

api = Blueprint("api", __name__)

def livedata_grafiek(column):
    # Get flexible minute range from request, default 1 minute, max 1440 (1 day)
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

    # Als er geen meetwaarde is
    if m is None:
        return jsonify({
            "pm25": 0,
            "pm10": 0,
            "pm1": 0,
            "aqi": 0,
            "co2": 0,
            "tvoc": 0,
            "status": {
                "pm25": "grey",
                "pm10": "grey",
                "pm1":  "grey",
                "aqi":  "grey",
                "co2":  "grey",
                "tvoc": "grey"
            }
        })

    # Nu is de gebruiker gegarandeerd ingelogd
    profiel = current_user.waardes.niveau
    status = bereken_status(m, profiel)

    return jsonify({
        "pm25": m.pm25,
        "pm10": m.pm10,
        "pm1": m.pm1,
        "aqi": m.aqi,
        "co2": m.co2,
        "tvoc": m.tvoc,
        "status": status
    })


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
    # Zoekt de geselecteerde patiënt op in de database
    patient = User.query.get_or_404(patient_id)
    
    # Bepaalt het risicoprofiel van deze patiënt
    profiel = "Laag"
    if patient.waardes and patient.waardes.niveau:
        profiel = patient.waardes.niveau

    # Haalt de specifieke drempelwaardes op uit config.py
    drempels = DREMPELWAARDES.get(profiel, DREMPELWAARDES["Laag"])

    # Genereert timestamps (labels) voor de afgelopen 7 metingen
    labels = []
    nu = datetime.now()
    for i in range(6, -1, -1):
        tijdstip = nu - timedelta(hours=i)
        labels.append(tijdstip.strftime("%H:%M")) # Direct geformatteerd als UU:MM voor Chart.js

    # Genereert dynamische testdata op basis van de drempels uit config.py
    pm25_rood_grens = drempels["PM2.5"]["oranje"][1]
    pm10_rood_grens = drempels["PM10"]["oranje"][1]
    
    pm25_data = [round(random.uniform(2, pm25_rood_grens + 8), 1) for _ in range(7)]
    pm10_data = [round(random.uniform(5, pm10_rood_grens + 15), 1) for _ in range(7)]
    no2_data = [round(random.uniform(10.0, 45.0), 1) for _ in range(7)]

    # Geeft de data terug in exact dezelfde Chart.js structuur ("labels" en "values")
    return jsonify({
        "labels": labels,
        "values": {
            "pm25": pm25_data,
            "pm10": pm10_data,
            "no2": no2_data
        },
        "profiel": profiel
    })