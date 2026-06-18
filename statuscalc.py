from config import DREMPELWAARDES
from datetime import datetime

#Update voor het nieuwe drempelwaardes format
def bepaal_status(sensor, waarde, profiel):
    drempels = DREMPELWAARDES[profiel][sensor]

    if waarde is None:
        return {"color": "grey", "status": "onbekend"}

    # Groen
    if drempels["groen_min"] <= waarde <= drempels["groen_max"]:
        return {"color": "green", "status": "goed"}

    # Oranje
    if drempels["oranje_min"] <= waarde <= drempels["oranje_max"]:
        return {"color": "orange", "status": "matig"}

    # Rood
    if waarde >= drempels["rood_min"]:
        return {"color": "red", "status": "slecht"}

    # Fallback (zou nooit moeten gebeuren)
    return {"color": "grey", "status": "onbekend"}


#Werkt met nieuwe drempelwaardesform
def bereken_status(meting, profiel):
    return {
        "pm25": bepaal_status("PM25", meting.pm25, profiel),
        "pm10": bepaal_status("PM10", meting.pm10, profiel),
        "pm1":  bepaal_status("PM1",  meting.pm1,  profiel),
        "co2":  bepaal_status("CO2",  meting.co2,  profiel),
        "tvoc": bepaal_status("TVOC", meting.tvoc, profiel),
        "aqi":  bepaal_status("AQI",  meting.aqi,  profiel),
    }


def group_status(colors):
    if "red" in colors:
        return "red"
    if colors.count("orange") >= 2:
        return "orange"
    return "green"


def eind_status(status):
    fijn = group_status([
        status["pm1"]["color"],
        status["pm25"]["color"],
        status["pm10"]["color"]
    ])

    gas = group_status([
        status["co2"]["color"],
        status["tvoc"]["color"],
        status["aqi"]["color"]
    ])

    if fijn == "red" or gas == "red":
        return "red"
    if fijn == "orange" or gas == "orange":
        return "orange"
    return "green"


def binnen_buiten_advies(kleur):
    if kleur == "red":
        return {"text": "Luchtkwaliteit is slecht", "icon": "house.png", "color": "advies-red"}
    if kleur == "orange":
        return {"text": "Luchtkwaliteit is matig", "icon": "house.png", "color": "advies-orange"}
    return {"text": "Luchtkwaliteit is goed", "icon": "sun.png", "color": "advies-green"}


def sport_advies(kleur):
    if kleur == "red":
        return {"text": "Pas op met bewegen", "icon": "no-sport.png", "color": "advies-red"}
    if kleur == "orange":
        return {"text": "Bewegen alleen rustig", "icon": "rest.png", "color": "advies-orange"}
    return {"text": "Bewegen kan hier goed", "icon": "sport.png", "color": "advies-green"}


#Helpfunctie voor volledige_status om de timedelta van de laatste meting te bepalen.
def tijdsverschil_tekst(timestamp):
    if not timestamp:
        return "Geen metingen"

    diff = (datetime.now() - timestamp).total_seconds()

    if diff < 60:
        return f"{int(diff)}s geleden"
    elif diff < 3600:
        return f"{int(diff // 60)} min geleden"
    else:
        return f"{int(diff // 3600)} uur geleden"


def volledige_status(meting, profiel):

    #Als er geen data is voor deze gebruiker:
    if meting is None:
        return {
            "values": {
                "pm1": None,
                "pm25": None,
                "pm10": None,
                "co2": None,
                "tvoc": None,
                "aqi": None
            },
            "status": {
                "pm1":  {"color": "grey", "status": "geen data"},
                "pm25": {"color": "grey", "status": "geen data"},
                "pm10": {"color": "grey", "status": "geen data"},
                "co2":  {"color": "grey", "status": "geen data"},
                "tvoc": {"color": "grey", "status": "geen data"},
                "aqi":  {"color": "grey", "status": "geen data"}
            },
            "groups": {
                "fijnstof": "grey",
                "gassen": "grey"
            },
            "eind": "grey",
            "advies": {
                "binnenbuiten": {
                    "text": "Geen data beschikbaar",
                    "icon": "house.png",
                    "color": "advies-grey"
                },
                "sport": {
                    "text": "Geen data beschikbaar",
                    "icon": "rest.png",
                    "color": "advies-grey"
                }
            },
            "measurement_timestamp": None,
            "measurement_age": "Geen metingen"
        }

    #Als er data is voor deze gebruiker...
    status = bereken_status(meting, profiel)
    eind = eind_status(status)

    return {
        "values": {
            "pm1": meting.pm1,
            "pm25": meting.pm25,
            "pm10": meting.pm10,
            "co2": meting.co2,
            "tvoc": meting.tvoc,
            "aqi": meting.aqi
        },
        "status": status,
        "groups": {
            "fijnstof": group_status([
                status["pm1"]["color"],
                status["pm25"]["color"],
                status["pm10"]["color"]
            ]),
            "gassen": group_status([
                status["co2"]["color"],
                status["tvoc"]["color"],
                status["aqi"]["color"]
            ])
        },
        "eind": eind,
        "advies": {
            "binnenbuiten": binnen_buiten_advies(eind),
            "sport": sport_advies(eind)
        },
        "measurement_timestamp": meting.timestamp.isoformat() if meting.timestamp else None,
        "measurement_age": tijdsverschil_tekst(meting.timestamp)
    }
