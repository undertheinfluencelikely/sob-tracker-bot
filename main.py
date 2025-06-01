from flask import Flask
from threading import Thread
import discord
from discord.ext import commands, tasks
from collections import defaultdict
from datetime import datetime, timedelta
import os
import pytz
import re
import random

# Flask server to keep Railway bot alive
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Globals
OWNER_ID = 1217191811559329792
crown_role_id = None
sob_counts = defaultdict(int)
last_champ = None
eastern = pytz.timezone("America/New_York")
uwu_targets = {}  # user_id: expiration_time or None

# Intents and bot setup
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# UwUify Function
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

# Events
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    weekly_reset.start()

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    if str(reaction.emoji) == "😭":
        message_author = reaction.message.author
        if message_author.id == user.id:
            print(f"⚠️ {user.name} tried to self-sob in #{reaction.message.channel.name}")
            return
        if not message_author.bot:
            sob_counts[message_author.id] += 1

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.bot:
        return

    if message.author.id in uwu_targets:
        expire_time = uwu_targets[message.author.id]
        if expire_time and datetime.utcnow() > expire_time:
            del uwu_targets[message.author.id]
            return
        cursed = ultra_uwuify(message.content)
        try:
            await message.channel.send(cursed)
        except:
            pass

# Commands
@bot.command()
async def sobboard(ctx):
    sorted_counts = sorted(sob_counts.items(), key=lambda x: x[1], reverse=True)
    leaderboard = ""
    for i, (user_id, count) in enumerate(sorted_counts[:10], start=1):
        user = await bot.fetch_user(user_id)
        leaderboard += f"{i}. {user.name}: {count} sobs\n"
    await ctx.send(f"😭 **Sob Leaderboard**\n{leaderboard or 'No sobs yet!'}")

@bot.command()
async def sobs(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    count = sob_counts.get(member.id, 0)
    await ctx.send(f"😭 **{member.display_name}** has received {count} sobs.")

@bot.command()
async def crown(ctx):
    if ctx.author.id != OWNER_ID:
        return
    await assign_sob_king()
    await ctx.send("👑 Crown assigned based on current sobs.")

@bot.command()
async def setcrown(ctx, role: discord.Role):
    if ctx.author.id != OWNER_ID:
        return
    global crown_role_id
    crown_role_id = role.id
    await ctx.send(f"👑 Crown role set to **{role.name}**.")

@bot.command()
async def sobreset(ctx):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("🚫 You don't have permission to reset sobs.")
    if crown_role_id and last_champ:
        guild = ctx.guild
        role = guild.get_role(crown_role_id)
        member = guild.get_member(last_champ)
        if role and member and role in member.roles:
            await member.remove_roles(role)
            print(f"👑 Removed crown from {member.display_name}")
    sob_counts.clear()
    globals()['last_champ'] = None
    await ctx.send("😭 All sob counts have been reset and the crown role has been cleared.")
    print("🔁 Manual sob reset triggered by owner.")

@bot.command()
async def uwu(ctx, member: discord.Member, duration: str = None):
    if ctx.author.id != OWNER_ID:
        return await ctx.message.delete()
    expire = None
    if duration:
        match = re.match(r'(\d+)([smhd])', duration.lower())
        if match:
            val, unit = int(match.group(1)), match.group(2)
            delta = {'s': timedelta(seconds=val), 'm': timedelta(minutes=val),
                     'h': timedelta(hours=val), 'd': timedelta(days=val)}
            expire = datetime.utcnow() + delta[unit]
    uwu_targets[member.id] = expire
    await ctx.message.delete()

@bot.command()
async def unuwu(ctx, member: discord.Member):
    if ctx.author.id != OWNER_ID:
        return await ctx.message.delete()
    if member.id in uwu_targets:
        del uwu_targets[member.id]
    await ctx.message.delete()

# Sob King Assignment
@tasks.loop(minutes=1)
async def weekly_reset():
    now = datetime.now(eastern)
    if now.weekday() == 6 and now.hour == 0 and now.minute == 0:
        print("Running weekly sob reset and crown transfer.")
        await assign_sob_king()
        sob_counts.clear()
        globals()['last_champ'] = None

async def assign_sob_king():
    global last_champ
    guild = bot.guilds[0]
    if not crown_role_id:
        print("Crown role not set.")
        return
    role = guild.get_role(crown_role_id)
    if not role:
        print("Crown role ID is invalid or role was deleted.")
        return
    if not sob_counts:
        print("No sobs recorded this week.")
        return
    top_user_id = max(sob_counts, key=sob_counts.get)
    member = guild.get_member(top_user_id)
    if member:
        await member.add_roles(role)
        print(f"Gave Sob King to {member.display_name}")
    if last_champ and last_champ != top_user_id:
        old_member = guild.get_member(last_champ)
        if old_member:
            await old_member.remove_roles(role)
            print(f"Removed Sob King from {old_member.display_name}")
    last_champ = top_user_id

# Keep alive + run bot
keep_alive()
TOKEN = os.environ['TOKEN']
bot.run(TOKEN)
