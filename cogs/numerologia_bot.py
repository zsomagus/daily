import discord
from discord import app_commands
from discord.ext import commands
from modulok import numerologia_full

class Numerologia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="num",
        description="Numerológiai elemzés generálása SVG formátumban"
    )
    @app_commands.describe
        name="Teljes név",
        date="Születési dátum (pl. 1976.03.15)",
        time="Születési idő (pl. 21:53)"
    )
    async def num(self, interaction: discord.Interaction, name: str, date: str, time: str):
        await interaction.response.defer(thinking=True)

        # Numerológiai fájlok generálása
        pdf_path, svg_path = numerologia_full.generate(name, date, time)

        # Privát üzenet küldése
        try:
            await interaction.user.send(
                f"📜 **{name}** numerológiai elemzése elkészült!\n"
                f"Itt tudod letölteni:",
                file=discord.File(pdf_path)
            )
            await interaction.followup.send("✅ Az elemzést privát üzenetben elküldtem neked.")
        except discord.Forbidden:
            await interaction.followup.send("⚠️ Nem tudtam privát üzenetet küldeni (DM letiltva).")

async def setup(bot):
    await bot.add_cog(Numerologia(bot))
