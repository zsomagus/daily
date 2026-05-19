import json

with open("mentett_adatok.json", "r", encoding="utf-8") as f:
    persons = json.load(f)

for p in persons:
    if "vezetek_nev" in p and "kereszt_nev" in p:
        p["name"] = f"{p['vezetek_nev']} {p['kereszt_nev']}"
        del p["vezetek_nev"]
        del p["kereszt_nev"]

    # magyar kulcsok átírása angolra
    if "datum" in p:
        p["date"] = p.pop("datum")
    if "ido" in p:
        p["time"] = p.pop("ido")
    if "latitude" in p:
        p["lat"] = p.pop("latitude")
    if "longitude" in p:
        p["lon"] = p.pop("longitude")
    if "ido_zona" in p:
        p["timezone"] = p.pop("ido_zona")
    if "nyari_idoszamitas" in p:
        p["dst"] = p.pop("nyari_idoszamitas")

with open("mentett_adatok.json", "w", encoding="utf-8") as f:
    json.dump(persons, f, ensure_ascii=False, indent=4)
