import pendulum
from modulok.astro_core import get_chart_data

def fill_prashna_data():
    now = pendulum.now("Europe/Budapest")

    date_str = now.format("YYYY-MM-DD")
    time_str = now.format("HH:mm")

    lat = 46.5126
    lon = 18.0912

    chart_data = get_chart_data(
        source="jyotishganit",
        name="Prashna",
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
        minute=now.minute,
        tz_str="Europe/Budapest",
        lng=lon,
        lat=lat,
        varga_name="D1"
    )

    return {
        "date": date_str,
        "time": time_str,
        "latitude": lat,
        "longitude": lon,
        "chart_data": chart_data
    }
