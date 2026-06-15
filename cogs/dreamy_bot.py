import os
import discord
from discord import app_commands
from discord.ext import commands

# Háttérfunkciók importálása a modulokból
from modulok.load_alomszotar import load_alomszotar
from modulok.music_prompt import build_music_prompt

class DreamyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Álomszótár automatikus betöltése indításkor
        self.szotar = load_alomszotar()

    def levag_ragokat(self, szo: str) -> str:
        """ Fagyásbiztos, intelligens magyar rageltávolító motor """
        szo_tisztitott = szo.lower().strip()
        
        # 1. Alapvető határozóragok és névutók listája
        ragok = ["ban", "ben", "val", "vel", "hoz", "hez", "höz",
                 "nak", "nek", "ból", "ből", "ről", "ről", "tól", "től",
                 "ra", "re", "ig", "ért", "vá", "vé"]
                 
        for rag in ragok:
            if szo_tisztitott.endswith(rag) and len(szo_tisztitott) > len(rag) + 2:
                szo_tisztitott = szo_tisztitott[:-len(rag)]
                break 
        
        # 2. Tárgyrag (-t) és Többes szám (-k) kezelése
        if len(szo_tisztitott) > 3:
            if szo_tisztitott.endswith("t") and szo_tisztitott[-2] in ["a", "e", "o", "ó", "é", "i"]:
                szo_tisztitott = szo_tisztitott[:-1]
            elif szo_tisztitott.endswith("k") and szo_tisztitott[-2] in ["o", "e", "ö", "a", "á", "é"]:
                szo_tisztitott = szo_tisztitott[:-1]

        # 3. Kötőhangzók korrigálása (pl. kutyá -> kutya)
        if len(szo_tisztitott) > 2:
            if szo_tisztitott.endswith("á"): szo_tisztitott = szo_tisztitott[:-1] + "a"
            elif szo_tisztitott.endswith("é"): szo_tisztitott = szo_tisztitott[:-1] + "e"
            elif szo_tisztitott.endswith("o") or szo_tisztitott.endswith("e"):
                if szo_tisztitott[-2] not in ["a", "e", "i", "o", "u"]:
                    szo_tisztitott = szo_tisztitott[:-1]

        return szo_tisztitott

    @app_commands.command(name="álom", description="Kielemezi az álmodat és elkészíti a zenei AI promptot.")
    @app_commands.describe(
        mit_álmodtál="Írd le részletesen az álmodat...",
        hangulat="Milyen érzés volt az álom? (pl. Félelmetes, Nyugodt, Rejtélyes)",
        kulcsszavak="Vesszővel elválasztott plusz kulcsszavak (opcionális)"
    )
    async def alom_parancs(self, interaction: discord.Interaction, mit_álmodtál: str, hangulat: str = "Nyugodt", kulcsszavak: str = ""):
        # Titkos válaszadás (csak a kérdező látja a saját elemzését)
        await interaction.response.defer(ephemeral=True)
        
        text = mit_álmodtál.strip()
        if not text:
            await interaction.followup.send("❌ Kérlek, írd le az álmodat szövegesen is!", ephemeral=True)
            return

        # === 🔮 ÁLOMSZÓTÁR MOTOR ===
        talalatok = []
        szimbolumok = []
        
        szavak = [s.strip().lower() for s in text.split() if len(s.strip()) > 2]
        szavak_tovei = [self.levag_ragokat(s) for s in szavak]

        egyedi_kulcsszavak = [k.strip().lower() for k in kulcsszavak.split(",") if k.strip()]
        minden_keresett_kifejezes = list(set(szavak_tovei + egyedi_kulcsszavak))

        if self.szotar:
            for szo in minden_keresett_kifejezes:
                if not szo or len(szo) < 3:
                    continue
                for item in self.szotar.get("alomszotar", []):
                    if isinstance(item, dict):
                        kulcsszo = item.get("kulcsszo", "").lower().strip()
                        
                        if szo == kulcsszo or kulcsszo in szo:
                            jelentesek = item.get("jelentesek", [])
                            for j in jelentesek:
                                sor = f"• **{kulcsszo.capitalize()}**: {j}"
                                if sor not in talalatok:
                                    talalatok.append(sor)
                            
                            if kulcsszo not in szimbolumok:
                                szimbolumok.append(kulcsszo)

        if talalatok:
            ertelmezes_szoveg = "\n".join(talalatok)
        else:
            ertelmezes_szoveg = (
                "❌ *Nincs közvetlen találat az álomszótárban.*\n"
                f"Próbált kulcsszavak a szövegedből: _{', '.join(minden_keresett_kifejezes)}_\n"
                "Tipp: Próbálj meg tőszavakat (pl. ablak, ház, víz, kutya) használni legközelebb!"
            )

        # ─── ZENEI AI PROMPT LÁNC ELŐÁLLÍTÁSA ───
        prompt_text = build_music_prompt(text, hangulat, kulcsszavak, szimbolumok)

        # Üzenet formázása és lezárása
        valasz = "✨ **KEDVES LÉLEK, ÍME AZ ÁLMOD PRIVÁT ELEMZÉSE** ✨\n\n"
        valasz += f"📝 **A te álmod:**\n_{text}_\n\n"
        valasz += f"🎭 **Álombeli hangulat:** `{hangulat}`\n"
        valasz += f"🏷️ **Feldolgozott szimbólumok:** {', '.join([s.capitalize() for s in szimbolumok]) if szimbolumok else 'Nem azonosítható'}\n\n"
        valasz += f"🔮 **SZIMBÓLUMOK JELENTÉSE:**\n{ertelmezes_szoveg}\n\n"
        valasz += "🎵 **ZENEI AI PROMPT LÁNC (Suno / Udio / MusicAI):**\n"
        valasz += f"```text\n{prompt_text}\n```\n"
        valasz += "*Ezt a promptot kimásolva azonnal generálhatsz egy meditációs zenét az álmod energiáiból!*"

        # Elküldjük az üzenetet (szigorúan titkosan, csak ő látja)
        await interaction.followup.send(valasz, ephemeral=True)

# Regisztráció a fő bot rendszerbe
async def setup(bot):
    await bot.add_cog(DreamyCog(bot))