import math

WEIGHT_MAP = {
    "intermittent": 1,
    "mild": 2,
    "matig": 4,
    "ernstig": 8,

    "g1": 2,
    "g2": 4,
    "g3": 8,
    "g4": 16,
}

def ziekte_score(diagnoses: dict):
    total = 0

    for disease, level in (diagnoses or {}).items():
        base = WEIGHT_MAP.get(level, 1)

        if disease == "copd":
            base *= 1.2

        if disease == "astma":
            base *= 1.0

        total += base ** 1.2   # 🔥 exponentieel effect

    return total


def calc_score(waardes):
    score = 0

    # basic factors
    score += waardes.rookt
    score += waardes.dag
    score += waardes.nacht
    score += waardes.saba
    score += waardes.beperking
    score += waardes.hospital
    score += waardes.prednison

    if waardes.leeftijd >= 65:
        score += 2

    score += waardes.exacerbaties * 2

    # 🔥 disease impact (BELANGRIJKSTE)
    score += ziekte_score(waardes.diagnose)

    return score


def calc_niveau(score):
    if score < 8:
        return "Laag"
    elif score < 18:
        return "Midden"
    return "Hoog"