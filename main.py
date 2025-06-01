import discord
from discord.ext import commands
from datetime import datetime, timedelta
import os
import re
import random

# === CONFIG ===
OWNER_ID = 1217191811559329792  # Your ID
TOKEN = os.environ['TOKEN']     # Or replace with a raw string if testing

# === BOT SETUP ===
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
uwu_targets = {}  # user_id: expiration time or None

# === UWUIFY FUNCTION ===
def ultra_uwuify(text):
    faces = ['👉👈', '>w<', '🥺', '😳', '💦', '💖', 'rawr~', 'uwu', 'X3', '~nyaa']
    text = re.sub(r'[rl]', 'w', text)
    text = re.sub(r'[RL]', 'W', text)
    text = re.sub(r'n([aeiou])', r'ny\1', text)
    text = re.sub(r'N([aeiouAEIOU])', r'Ny\1', text)
    stutter = lambda w: w[0] + '-' + w if random.random() < 0.2 else w
    text = ' '.join([stutter(word) for word in text.split()])
    emoji_spam = ' ' + ' '.join(random.sample(faces, 3))
    return f"*{text}*{emoji_spam}"

# === EVENTS ===
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.bot:
        return

    print(f"[msg] {message.author}: {message.content}")

    if message.author.id in uwu_targets:
        expire_time = uwu_targets[message.author.id]
        if expire_time and datetime.utcnow() > expire_time:
            del uwu_targets[message.author.id]
            print(f"[uwu] expired for {message.author}")
            return
        cursed = ultra_uwuify(message.content)
        try:
            await message.channel.send(cursed)
            print(f"[uwu] mocked {message.author}")
        except Exception as e:
            print(f"[error] uwu response failed: {e}")

# === COMMANDS ===
@bot.command()
async def uwu(ctx, member: discord.Member, duration: str = None):
    if ctx.author.id != OWNER_ID:
        return
    expire = None
    if duration:
        match = re.match(r'(\d+)([smhd])', duration.lower())
        if match:
            val, unit = int(match.group(1)), match.group(2)
            delta = {'s': timedelta(seconds=val), 'm': timedelta(minutes=val),
                     'h': timedelta(hours=val), 'd': timedelta(days=val)}
            expire = datetime.utcnow() + delta[unit]
    uwu_targets[member.id] = expire
    print(f"[cmd] {member} added to uwu_targets until {expire}")
    await ctx.message.delete()

@bot.command()
async def unuwu(ctx, member: discord.Member):
    if ctx.author.id != OWNER_ID:
        return
    if member.id in uwu_targets:
        del uwu_targets[member.id]
        print(f"[cmd] {member} removed from uwu_targets")
    await ctx.message.delete()

# === RUN ===
bot.run(TOKEN)
