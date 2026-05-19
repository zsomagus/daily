import discord
from discord.ext import commands
import json
import os

TOKEN = "IDE_A_TOKENED"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"

# --------------------------
# ADATKEZELÉS
# --------------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

data = load_data()

# --------------------------
# AUTOMATIKUS TANÍTVÁNY
# --------------------------

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name="Tanítvány")
    if role:
        await member.add_roles(role)

# --------------------------
# AKTIVITÁS FIGYELÉS
# --------------------------

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)

    if user_id not in data:
        data[user_id] = {
            "points": 0,
            "flagged_for_beavatott": False
        }

    data[user_id]["points"] += 1
    save_data(data)

    # 30 üzenet után jelölés Beavatottnak
    if (
        data[user_id]["points"] >= 30 and
        not data[user_id]["flagged_for_beavatott"]
    ):
        data[user_id]["flagged_for_beavatott"] = True
        save_data(data)

        await message.channel.send(
            f"🜂 {message.author.mention} készen áll a Beavatásra.\n"
            "Egy Őrző hamarosan döntést hoz."
        )

    await bot.process_commands(message)

# --------------------------
# MANUÁLIS BEAVATÁS
# --------------------------

@bot.command()
@commands.has_role("Őrző")
async def beavat(ctx, member: discord.Member):

    beavatott_role = discord.utils.get(ctx.guild.roles, name="Beavatott")
    if beavatott_role:
        await member.add_roles(beavatott_role)

        await ctx.send(
            f"🜏 {member.mention} beavatása megtörtént.\n"
            "Mostantól hozzáfér a Belső Műhelyhez."
        )

# --------------------------
# ORÁKULUM MÓD
# --------------------------

@bot.command()
async def orakulum(ctx, *, kerdes):

    valasz = (
        "🜄 Az ég tükrében minden kérdés önmagadra mutat.\n"
        "Figyeld meg, hol ismétlődik ez a minta az életedben."
    )

    await ctx.send(valasz)

# --------------------------
# JYOTISHGANIT ELŐKÉSZÍTÉS
# --------------------------

@bot.command()
async def elemzes(ctx, datum, ido, hely):

    try:
        from jyotishganit import calculate_chart

        chart = calculate_chart(datum, ido, hely)

        await ctx.send(
            f"🜂 A képleted főbb elemei:\n{chart}"
        )

    except Exception as e:
        await ctx.send("Hiba történt az elemzés során.")
        print(e)

# --------------------------
@bot.event
async def on_ready():
    print(f"Ébredés aktív: {bot.user}")

bot.run(TOKEN)
