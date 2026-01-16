# ================= RENDER KEEP-ALIVE WEB SERVER =================
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

# ================= DISCORD BOT =================
import discord
from discord import app_commands
from discord.ext import commands
import asyncio

# ================= GEMINI =================
import google.generativeai as genai

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not TOKEN:
    raise RuntimeError("❌ TOKEN is not set in environment variables!")
if not GEMINI_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY is not set in environment variables!")

genai.configure(api_key=GEMINI_KEY)

# Use safe model
model = genai.GenerativeModel("gemini-pro")

# ================= BOT SETUP =================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# guild_id -> set(user_ids)
uwu_locked_users = {}

# ================= AI FUNCTION =================
async def ai_uwuify(text: str) -> str:
    prompt = f"""
Rewrite the following message in a cute anime "uwu" style.
Keep the SAME MEANING, SAME INTENT, SAME EMOTION.
If it's angry, keep it angry. If it's toxic, keep it toxic. If it's normal, keep it normal.
Just rewrite the wording into uwu/anime style.

Message:
{text}
"""

    loop = asyncio.get_event_loop()

    def call_ai():
        resp = model.generate_content(prompt)
        return resp.text

    result = await loop.run_in_executor(None, call_ai)
    return result.strip()

# ================= EVENTS =================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Commands synced: {len(synced)}")
    except Exception as e:
        print("❌ Sync error:", e)

@bot.event
async def on_message(message: discord.Message):
    # Debug: confirm messages are seen
    print("MESSAGE SEEN:", message.author, repr(message.content))

    if message.author.bot:
        return

    if not message.guild:
        return

    guild_id = message.guild.id
    user_id = message.author.id

    if guild_id in uwu_locked_users and user_id in uwu_locked_users[guild_id]:
        if not message.content.strip():
            return

        try:
            uwu_text = await ai_uwuify(message.content)

            # Try deleting original
            try:
                await message.delete()
            except Exception as e:
                print("❌ Delete failed:", repr(e))

            await message.channel.send(
                f"**{message.author.display_name} says:** {uwu_text}"
            )

        except Exception as e:
            print("❌ AI ERROR:", repr(e))

    await bot.process_commands(message)

# ================= COMMANDS =================
@bot.tree.command(name="uwu_lock", description="Curse a user with AI UwU speech")
@app_commands.checks.has_permissions(administrator=True)
async def uwu_lock(interaction: discord.Interaction, user: discord.Member):
    guild_id = interaction.guild.id

    if guild_id not in uwu_locked_users:
        uwu_locked_users[guild_id] = set()

    uwu_locked_users[guild_id].add(user.id)

    await interaction.response.send_message(
        f"🔒 **{user.mention} has been AI-UwU cursed.** 😈"
    )

@bot.tree.command(name="uwu_unlock", description="Remove UwU curse from user")
@app_commands.checks.has_permissions(administrator=True)
async def uwu_unlock(interaction: discord.Interaction, user: discord.Member):
    guild_id = interaction.guild.id

    if guild_id in uwu_locked_users:
        uwu_locked_users[guild_id].discard(user.id)

    await interaction.response.send_message(
        f"🔓 **{user.mention} is free.** 🗿"
    )

# ================= START =================
bot.run(TOKEN)
