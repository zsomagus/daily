import sys
from PyQt5.QtWidgets import QApplication
from gui import main_gui 
from modulok.astro_core import get_chart_data
import pendulum

app = QApplication(sys.argv)

# aktuális időpont efemerida
now = pendulum.now("Europe/Budapest")
planet_positions = get_chart_data()  # vagy last_planet_positions(now)

# átadás a GUI‑nak
window = main_gui(planet_positions)
window.show()

sys.exit(app.exec_())
