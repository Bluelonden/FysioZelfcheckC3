from config import DREMPELWAARDES

def bepaal_status(sensor, waarde, profiel):
    """
    Bepaal status met zowel kleurcodes (HEAD) als Nederlands descriptoren (Base).
    Return dict met beide formaten voor maximale compatibiliteit.
    """
    drempels = DREMPELWAARDES[profiel][sensor]

    if waarde is None:
        return {"color": "grey", "status": "onbekend"}

    # Check groene zone
    if drempels["groen"][0] <= waarde <= drempels["groen"][1]:
        return {"color": "green", "status": "goed"}

    # Check oranje zone
    if drempels["oranje"][0] <= waarde <= drempels["oranje"][1]:
        return {"color": "orange", "status": "matig"}

    # Rood/slecht
    return {"color": "red", "status": "slecht"}


def bereken_status(meting, profiel):
    """
    Bereken status voor alle sensoren - geeft kleurcodes en Nederlandse descriptoren.
    """
    return {
        "pm25": bepaal_status("PM2.5", meting.pm25, profiel),
        "pm10": bepaal_status("PM10", meting.pm10, profiel),
        "pm1":  bepaal_status("PM1",  meting.pm1,  profiel),
        "co2":  bepaal_status("CO2",  meting.co2,  profiel),
        "tvoc": bepaal_status("TVOC", meting.tvoc, profiel),
        "aqi":  bepaal_status("AQI",  meting.aqi,  profiel),
    }
