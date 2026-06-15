import os
import datetime
import discord
from discord import app_commands
from discord.ext import commands
import pandas as pd
import jyotishganit

# Globális koordináták a Tithi számításhoz (Budapest)
LAT = 46.85725
LON = 18.15341

class NapiappCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Ide írhatod be a szoba korlátozást, ha szeretnéd (számként)
        # Ha mindegyik szobában engedni akarod, hagyd None-on!
        self.target_channel_id = 1499057233529671752

    # --- CSATORNA ELLENŐRZŐ SEGÉDFÜGGVÉNY ---
    def is_correct_channel(self, interaction: discord.Interaction) -> bool:
        if self.target_channel_id is not None and interaction.channel_id != self.target_channel_id:
            return False
        return True

    # --- SAKK-REKKER HELYI FUNKCIÓI ---
    def load_tithi_data(self):
        tithi_dict = {}
        file_name = "tithi_ajánlások.xlsx"
        if not os.path.exists(file_name):
            return None
        with open(file_name, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        import re
        matches = re.findall(r'(\d+)\s*,\s*(Shukla|Krishna)\s*,\s*([A-Za-z]+)\s*,\s*([^,\n]+),([^,\n]+)', content)
        for m in matches:
            tithi_dict[int(m[0])] = {
                "tipus": m[1].strip(), "nev": m[2].strip(),
                "jelentes": m[3].replace('"', '').strip(), "ajanlas": m[4].replace('"', '').strip()
            }
        return tithi_dict

    def get_current_tithi_index(self):
        try:
            now = datetime.datetime.now()
            tz_offset = datetime.datetime.now().astimezone().utcoffset().total_seconds() / 3600.0
            tithi_index = jyotishganit.get_tithi(
                year=now.year, month=now.month, day=now.day, 
                hour=now.hour, minute=now.minute, lat=LAT, lon=LON, tz=tz_offset
            )
            if isinstance(tithi_index, int) and 1 <= tithi_index <= 30:
                return tithi_index
            return getattr(tithi_index, 'index', 1)
        except Exception:
            base_date = datetime.date(2026, 3, 19)
            return ((datetime.date.today() - base_date).days % 30) + 1

    def generate_message(self, current_idx, tithis):
        tithi_info = {"tipus": "Shukla", "nev": "Pratipada", "jelentes": "Új kezdet", "ajanlas": "Célok megfogalmazása."}
        if tithis and current_idx in tithis:
            tithi_info = tithis[current_idx]
        ma_szoveg = datetime.date.today().strftime('%Y. %B %d.')
        
        return f"""```text
==============================================================================
                ✨ JÓ REGGELT, KEDVES LÉLEK! ✨
==============================================================================
Dátum: {ma_szoveg}
"Amilyen a belső világod, olyan a csillagos égbolt is feletted."

🌙 A HOLD AKTUÁLIS ÁLLAPOTA (TITHI):
   Ma a Hold a(z) {tithi_info['tipus']} {tithi_info['nev']} fázisában jàr (Tithi sorszám: {current_idx}).
   Energetikai jelentés: {tithi_info['jelentes']}

🪐 TRANZITOK ÉS PURUSHARTHA ÚTMUTATÁS:
   A Graha (bolygó) állások emlékeztetnek, hogy a belső béke (Sattva) megőrzése 
   a legnagyobb Dharma. A tranzitok finoman támogatják a Moksha felé tett lépéseidet.

🌱 NAPI AJÁNLÁS A LÉLEKNEK:
   * Tithi gyakorlat: {tithi_info['ajanlas']}
   * Mantra a mai napra: "Összhangban vagyok a kozmosz ritmusával."
------------------------------------------------------------------------------
```"""

    def get_yantra_path(self, tithi_idx):
        yantra_dir = "yantra"
        if not os.path.exists(yantra_dir):
            return None
        prefix = f"{tithi_idx} "
        for file in os.listdir(yantra_dir):
            if file.startswith(prefix) and file.lower().endswith(('.jpg', '.jpeg', '.png')):
                return os.path.join(yantra_dir, file)
        return None

    # --- 1. /hold PARANCS ---
    @app_commands.command(name="hold", description="Megmutatja az aktuális Tithi holdfázist és a napi lelki útravalót.")
    async def hold_command(self, interaction: discord.Interaction):
        if not self.is_correct_channel(interaction):
            await interaction.response.send_message("✨ Ezt a parancsot csak a kijelölt belépési szobában használhatod!", ephemeral=True)
            return
            
        await interaction.response.defer()
        current_idx = self.get_current_tithi_index()
        tithis = self.load_tithi_data()
        message = self.generate_message(current_idx, tithis)
        await interaction.followup.send(message)

    # --- 2. /yantra PARANCS ---
    @app_commands.command(name="yantra", description="Megjeleníti a mai Tithihez tartozó szent Yantra meditációs képet.")
    async def yantra_command(self, interaction: discord.Interaction):
        if not self.is_correct_channel(interaction):
            await interaction.response.send_message("✨ Ezt a parancsot csak a kijelölt belépési szobában használhatod!", ephemeral=True)
            return

        await interaction.response.defer()
        current_idx = self.get_current_tithi_index()
        img_path = self.get_yantra_path(current_idx)
        
        if img_path and os.path.exists(img_path):
            file = discord.File(img_path, filename=os.path.basename(img_path))
            await interaction.followup.send(
                content=f"💮 **A mai nap szent geometriája (Tithi sorszám: {current_idx}):**\n*Helyezkedj el kényelmesen, és engedd, hogy a Yantra energiája lecsendesítse az elmédet.*", 
                file=file
            )
        else:
            await interaction.followup.send(f"❌ Sajnos a(z) {current_idx}. Tithihez tartozó Yantra kép nem található a szerveren.")

# Regisztrációs belépési pont a main_discord.py-hoz
async def setup(bot):
    await bot.add_cog(NapiappCog(bot))