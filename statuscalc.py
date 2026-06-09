from config import DREMPELWAARDES

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
        return {"text": "Blijf binnen", "icon": "house.png", "color": "advies-red"}
    if kleur == "orange":
        return {"text": "Liever binnen", "icon": "house.png", "color": "advies-orange"}
    return {"text": "Buiten is gezond", "icon": "sun.png", "color": "advies-green"}


def sport_advies(kleur):
    if kleur == "red":
        return {"text": "Niet sporten", "icon": "no-sport.png", "color": "advies-red"}
    if kleur == "orange":
        return {"text": "Beweeg rustig", "icon": "rest.png", "color": "advies-orange"}
    return {"text": "Sporten kan nu", "icon": "sport.png", "color": "advies-green"}


def volledige_status(meting, profiel):
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
        }
    }
