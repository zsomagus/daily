from datetime import datetime
from jyotishganit import calculate_birth_chart, get_birth_chart_json_string
from modulok import sonic_bridge
# Generate a complete Vedic birth chart
chart = calculate_birth_chart(
    birth_date=datetime(1976, 3, 15, 21, 53, 0),
    latitude=47.30,      # Correct for Hungary
    longitude=19.05,
    timezone_offset=2
)
dashas = chart.dashas
# Access key astrological data
print(f"Ascendant: {chart.d1_chart.houses[0].sign}")

# Safer: access Moon by name
#print(f"Moon Sign: {chart.d1_chart.planets['Moon'].sign}")

panchanga = chart.panchanga
print(f"Tithi: {panchanga.tithi}")
print(f"Nakshatra: {panchanga.nakshatra}")
print(f"Yoga: {panchanga.yoga}")
print(f"Karana: {panchanga.karana}")
print(f"Vaara: {panchanga.vaara}")
print('\n\n'.join(['Mahadasha: %s\n  Start: %s\n  End:   %s' % (lord, md['start'], md['end']) for lord, md in list(dashas.upcoming['mahadashas'].items())[:3]]))

# Save the entire chart as JSON
with open("birth_chart.json", "w") as json_file:
    json_file.write(get_birth_chart_json_string(chart))

print("Birth chart saved to birth_chart.json")
