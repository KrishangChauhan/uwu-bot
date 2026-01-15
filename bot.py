# ---- FAKE WEB SERVER FOR RENDER ----
from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "UwU bot is alive 😈"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web).start()

# ---- DISCORD BOT ----
import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
import asyncio

# ---- CONFIG ----
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---- GEMINI SETUP ----
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise RuntimeError("GEMINI_API_KEY not set!")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# { guild_id: set(user_ids) }
uwu_locked_users = {}

# ---- AI UWU FUNCTION ----
async def ai_uwuify(text: str) -> str:
    prompt = f"""
Rewrite the following message in a cute, anime "uwu" style.
Keep the SAME MEANING, SAME EMOTION, SAME INTENT.
If it's angry, keep it angry. If it's threatening, keep it threatening. If it's normal, keep it normal.
Just rewrite the language into uwu/anime style.

Message:
{text}
"""

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, lambda: model.generate_content(prompt)
    )

    return response.text.strip()

# ---- EVENTS ----
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.tree.sync()
    print("✅ Commands synced")

@bot.event
async def on_message(message: discord.Message):
    print("MESSAGE SEEN:", message.author, repr(message.content))
    if message.author.bot or not message.guild:
        return

    guild_id = message.guild.id
    user_id = message.author.id

    if guild_id in uwu_locked_users and user_id in uwu_locked_users[guild_id]:
        if not message.content.strip():
            return

        try:
            uwu_text = await ai_uwuify(message.content)

            await message.delete()
            await message.channel.send(
                f"**{message.author.display_name} says:** {uwu_text}"
            )
        except Exception as e:
            print("AI error:", e)

    await bot.process_commands(message)

# ---- COMMANDS ----
@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(name="uwu_lock", description="Curse a user with AI UwU speech")
async def uwu_lock(interaction: discord.Interaction, user: discord.Member):
    guild_id = interaction.guild.id
    if guild_id not in uwu_locked_users:
        uwu_locked_users[guild_id] = set()

    uwu_locked_users[guild_id].add(user.id)

    await interaction.response.send_message(
        f"🔒 **{user.mention} has been AI-UwU cursed.** 😈"
    )

@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(name="uwu_unlock", description="Remove UwU curse from user")
async def uwu_unlock(interaction: discord.Interaction, user: discord.Member):
    guild_id = interaction.guild.id
    if guild_id in uwu_locked_users:
        uwu_locked_users[guild_id].discard(user.id)

    await interaction.response.send_message(
        f"🔓 **{user.mention} is free.** 🗿"
    )

# ---- START ----
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN not set!")

bot.run(TOKEN)
