
from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from plotly.graph_objs import Figure, Scatter
from models import Metingen
from statuscalc import bereken_status
from datetime import datetime, timedelta

api = Blueprint("api", __name__)

def livedata_grafiek(column, title, y_label):

    laatste_uur = datetime.now() - timedelta(hours=1)
    metingen = (Metingen.query.filter(Metingen.timestamp >= laatste_uur).order_by(Metingen.timestamp.asc()).all())

    x = [m.timestamp for m in metingen]
    y = [getattr(m, column) for m in metingen]

    fig = Figure()

    fig.add_trace(Scatter(
        x=x,
        y=y,
        mode="lines+markers"
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Tijd",
        yaxis_title=y_label,
        showlegend= False
    )

    return fig.to_json()


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
    return livedata_grafiek("pm25", "PM2.5", "µg/m³")

@api.route("/pm10_fig")
def pm10_fig():
    return livedata_grafiek("pm10", "PM10", "µg/m³")

@api.route("/pm1_fig")
def pm1_fig():
    return livedata_grafiek("pm1", "PM1", "µg/m³")

@api.route("/aqi_fig")
def aqi_fig():
    return livedata_grafiek("aqi", "AQI", "Index")

@api.route("/co2_fig")
def co2_fig():
    return livedata_grafiek("co2", "CO₂", "ppm")

@api.route("/tvoc_fig")
def tvoc_fig():
    return livedata_grafiek("tvoc", "TVOC", "ppb")
