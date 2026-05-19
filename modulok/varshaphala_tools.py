# modulok/varshaphala_tools.py

import pendulum
from jyotishganit import calculate_birth_chart
from modulok import astro_core

def find_solar_return_datetime(birth_dt, age, lat, lon):
    """
    Megkeresi azt az időpontot, amikor a Nap visszatér
    a születési hosszúságra (Varshaphala).
    """

    # 1) Születési Nap pozíció
    birth_chart = calculate_birth_chart(
        birth_date=birth_dt.datetime(),
        latitude=lat,
        longitude=lon,
        timezone_offset=birth_dt.utcoffset().total_seconds() / 3600
    )
    target_long = birth_chart.planet_data["Sun"].longitude

    # 2) Célév
    approx = birth_dt.add(years=age)

    # 3) Iteráció ±48 órában, 10 perces lépésekben
    best_dt = None
    best_diff = 999

    for minutes in range(-48 * 60, 48 * 60, 10):
        test_dt = approx.add(minutes=minutes)

        chart = calculate_birth_chart(
            birth_date=test_dt.datetime(),
            latitude=lat,
            longitude=lon,
            timezone_offset=test_dt.utcoffset().total_seconds() / 3600
        )

        sun_long = chart.planet_data["Sun"].longitude
        diff = abs((sun_long - target_long + 180) % 360 - 180)

        if diff < best_diff:
            best_diff = diff
            best_dt = test_dt

    return best_dt


def compute_varshaphala_chart(birth_dt, age, lat, lon):
    """
    Visszaadja a Varshaphala horoszkóp teljes adatait.
    """

    solar_return_dt = find_solar_return_datetime(birth_dt, age, lat, lon)

    chart = calculate_birth_chart(
        birth_date=solar_return_dt.datetime(),
        latitude=lat,
        longitude=lon,
        timezone_offset=solar_return_dt.utcoffset().total_seconds() / 3600
    )

    return {
        "datetime": solar_return_dt,
        "chart": chart,
        "planet_data": chart.planet_data,
        "tithi": chart.panchanga.tithi,
        "nakshatra": chart.panchanga.nakshatra,
        "yoga": chart.panchanga.yoga,
        "karana": chart.panchanga.karana,
        "vaara": chart.panchanga.vaara,
    }
