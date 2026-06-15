import os
import discord
from discord.ext import commands

# Token és alapbeállítások
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

class KözösségiBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        # A commands.Bot-ot használjuk, mert ez kezeli a Cog-okat
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Automatikusan betöltünk minden Python fájlt a cogs mappából
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"⚙️ {filename} sikeresen betöltve!")
                except Exception as e:
                    print(f"❌ Hiba a {filename} betöltésekor: {e}")

        # Szinkronizáljuk a Slash (/) parancsokat a Discorddal
        await self.tree.sync()


    async def on_ready(self):
        print(f"✨ A bot online! Név: {self.user.name}")

bot = KözösségiBot()
bot.run(DISCORD_TOKEN)