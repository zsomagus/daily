# main.py
import sys
import os

# GUI mappa hozzáadása a Python útvonalhoz
sys.path.append(os.path.join(os.path.dirname(__file__), "gui"))

from gui.gui_main import start_gui

if __name__ == "__main__":
    # Alapértelmezett üres adatok létrehozása, hogy a GUI hiba nélkül elindulhasson
    person_name = ""
    
    birth_data = {
        "vezeteknev": "",
        "keresztnev": "",
        "date_str": "1990-01-01",  # egy alapértelmezett induló dátum
        "time_str": "12:00",        # egy alapértelmezett induló időpont
        "timezone_str": "Europe/Budapest",
        "latitude": "47.4979",      # Budapest koordinátái alapértelmezettnek
        "longitude": "19.0402"
    }

    # Most már biztonságosan átadhatók a változók, nem dob NameError-t!
    start_gui()