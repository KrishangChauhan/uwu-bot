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

import discord
from discord import app_commands
from discord.ext import commands
import re
import unicodedata
import os

# ---- CONFIG ----
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# { guild_id: set(user_ids) }
uwu_locked_users = {}

# ---- TEXT NORMALIZATION (ANTI-BYPASS) ----
def normalize_text(text: str) -> str:
    # Convert fancy unicode fonts to normal
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # Remove zero-width and weird invisible chars
    text = re.sub(r"[\u200b-\u200f\u202a-\u202e]", "", text)

    return text

# ---- UWUIFIER ----
def uwuify(text: str) -> str:
    text = normalize_text(text)
    text = text.lower()

    # Basic replacements
    text = re.sub(r"[lr]", "w", text)
    text = re.sub(r"th", "d", text)
    text = re.sub(r"ove", "uv", text)

    # nya-ification
    text = re.sub(r"\bna", "nya", text)
    text = re.sub(r"\bne", "nye", text)
    text = re.sub(r"\bni", "nyi", text)
    text = re.sub(r"\bno", "nyo", text)
    text = re.sub(r"\bnu", "nyu", text)

    # Stutter sometimes
    text = re.sub(r"\b([a-z])", r"\1-\1", text, count=1)

    faces = [" UwU", " >_<", " (｡♥‿♥｡)", " 🥺👉👈", " (≧◡≦) ♡"]
    return text + faces[hash(text) % len(faces)]

# ---- EVENTS ----
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print("❌ Sync error:", e)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if not message.guild:
        return

    guild_id = message.guild.id
    user_id = message.author.id

    if guild_id in uwu_locked_users and user_id in uwu_locked_users[guild_id]:
        # If message is empty or only attachments, ignore
        if not message.content.strip():
            return

        try:
            uwu_text = uwuify(message.content)

            await message.delete()
            await message.channel.send(
                f"**{message.author.display_name} says:** {uwu_text}"
            )
        except discord.Forbidden:
            print("❌ Missing permissions to delete/send messages.")
        except Exception as e:
            print("❌ Error in uwu message handling:", e)

    await bot.process_commands(message)

# ---- SLASH COMMANDS ----

@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(name="uwu_lock", description="Curse a user with UwU speech")
async def uwu_lock(interaction: discord.Interaction, user: discord.Member):
    guild_id = interaction.guild.id

    if guild_id not in uwu_locked_users:
        uwu_locked_users[guild_id] = set()

    uwu_locked_users[guild_id].add(user.id)

    await interaction.response.send_message(
        f"🔒 **{user.mention} has been UwU cursed. There is no escape.** 🥺",
        ephemeral=False
    )

@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(name="uwu_unlock", description="Remove UwU curse from a user")
async def uwu_unlock(interaction: discord.Interaction, user: discord.Member):
    guild_id = interaction.guild.id

    if guild_id in uwu_locked_users:
        uwu_locked_users[guild_id].discard(user.id)

    await interaction.response.send_message(
        f"🔓 **{user.mention} is free. They may speak human again.** 🗿",
        ephemeral=False
    )

# ---- START BOT ----
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("❌ TOKEN environment variable not set!")

bot.run(TOKEN)
