from config import DREMPELWAARDES

def bepaal_status(sensor, waarde, profiel):
    # Bijvoorbeeld: user1 => Laag sensor => PM2.5
    # Dan krijg je dat deel van de dict met drempelwaardes
    drempels = DREMPELWAARDES[profiel][sensor]

    # waarde is hier de laatste meting
    if waarde is None:
        return "onbekend"  

    # binnen groene zone → goed
    if drempels["groen"][0] <= waarde <= drempels["groen"][1]:
        return "goed"     

    # binnen oranje zone → matig
    if drempels["oranje"][0] <= waarde <= drempels["oranje"][1]:
        return "matig"    

    # anders → slecht
    return "slecht"         


def bereken_status(meting, profiel):
    # Geeft voor elke sensor de status terug op basis van drempelwaardes
    return {
        "pm25": bepaal_status("PM2.5", meting.pm25, profiel),
        "pm10": bepaal_status("PM10", meting.pm10, profiel),
        "pm1":  bepaal_status("PM1",  meting.pm1,  profiel),
        "co2":  bepaal_status("CO2",  meting.co2,  profiel),
        "tvoc": bepaal_status("TVOC", meting.tvoc, profiel),
        "aqi":  bepaal_status("AQI",  meting.aqi,  profiel),
    }


def bereken_status(meting, profiel):
    return {
        "pm25": bepaal_status("PM2.5", meting.pm25, profiel),
        "pm10": bepaal_status("PM10", meting.pm10, profiel),
        "pm1":  bepaal_status("PM1",  meting.pm1,  profiel),
        "co2":  bepaal_status("CO2",  meting.co2,  profiel),
        "tvoc": bepaal_status("TVOC", meting.tvoc, profiel),
        "aqi":  bepaal_status("AQI",  meting.aqi,  profiel),
    }
