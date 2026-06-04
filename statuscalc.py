from config import DREMPELWAARDES


def bepaal_status(sensor, waarde, profiel):
    #Bijvoorbeeld user1 => Laag sensor => PM2.5 dan krijg je dat deel van de dict
    drempels = DREMPELWAARDES[profiel][sensor]

    #waarde is hier de laatste meting 
    if waarde is None:
        return "grey"

    if drempels["groen"][0] <= waarde <= drempels["groen"][1]:
        return "green"

    if drempels["oranje"][0] <= waarde <= drempels["oranje"][1]:
        return "orange"

    return "red"


def bereken_status(meting, profiel):
    return {
        "pm25": bepaal_status("PM2.5", meting.pm25, profiel),
        "pm10": bepaal_status("PM10", meting.pm10, profiel),
        "pm1":  bepaal_status("PM1",  meting.pm1,  profiel),
        "co2":  bepaal_status("CO2",  meting.co2,  profiel),
        "tvoc": bepaal_status("TVOC", meting.tvoc, profiel),
        "aqi":  bepaal_status("AQI",  meting.aqi,  profiel),
    }
