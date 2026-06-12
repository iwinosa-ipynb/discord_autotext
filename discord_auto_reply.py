# ⚠️ EDUCATIONAL PURPOSES ONLY
# Self-bots violate Discord's Terms of Service.
# Do NOT use this on a real account — for demonstration only.

# INSTALL: pip install discord.py-self python-dotenv

import discord
import asyncio
import random
import time
from datetime import datetime, date
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("DISCORD_USER_TOKEN")

# ── CONFIG ────────────────────────────────────────────────

# Right click your SERVER name → Copy Server ID
MONITORED_SERVER    = 1274909375584014336        # ← paste your server ID here e.g. 123456789012345678

# Right click a CHANNEL → Copy Channel ID (for proactive messages)
PROACTIVE_CHANNEL   = 1278965518270726185        # ← paste your channel ID here e.g. 987654321098765432

DAILY_LIMIT         = 450
MIN_DELAY           = 50       # min seconds before replying
MAX_DELAY           = 120       # max seconds before replying
COOLDOWN            = 100      # seconds between messages
IDLE_THRESHOLD      = 200      # seconds idle before proactive message

# ── WORD LISTS ────────────────────────────────────────────

REPLIES = [
    "yeah bro what's up",
    "lol true",
    "nah fr",
    "bro same",
    "wait what 😭",
    "lol",
    "say less",
    "no way bro",
    "facts",
    "idk man",
    "bro stop 💀",
    "achaa",
    "that's crazy",
    "cool",
    "bro im buusy",
    "wait",
    "lowkey yeah",
    "maybe",
    "bro chill 😭",
    "aight bet",
    "hold on",
    "okay",
    "nah",
    "lmao💀",
    "i fw that",
    "ok",
    "lwkmd",
    
]

PROACTIVE_MESSAGES = [
    "yo what you been up to",
    "aye you alive?",
    " bro say something",
    " what strategy youusing ",
    "what's good",
    "been quiet lately",
    "lfg",
    "you eaten?",
    "howfar?",
    "whats the update",
    "what are you doing today",
    "whats good",
    "hey",
    "holla",

]

# ── STATE ─────────────────────────────────────────────────

client           = discord.Client()
message_queue    = asyncio.Queue()
daily_count      = 0
last_reset       = date.today()
last_activity_at = 0
already_messaged = set()

# ── HELPERS ───────────────────────────────────────────────

def check_reset():
    global daily_count, last_reset, already_messaged
    if date.today() != last_reset:
        print(f"[{datetime.now()}] Midnight reset — count was {daily_count}")
        daily_count      = 0
        last_reset       = date.today()
        already_messaged = set()

def can_send():
    check_reset()
    return daily_count < DAILY_LIMIT

def get_monitored_guild():
    for guild in client.guilds:
        if guild.id == MONITORED_SERVER:
            return guild
    return None

def pick_random_member(guild):
    candidates = [
        m for m in guild.members
        if m != client.user
        and not m.bot
        and m.id not in already_messaged
    ]
    return random.choice(candidates) if candidates else None

def get_proactive_channel(guild):
    return guild.get_channel(PROACTIVE_CHANNEL)

# ── QUEUE PROCESSOR ───────────────────────────────────────

async def process_queue():
    global daily_count

    while True:
        message = await message_queue.get()

        if not can_send():
            print("[LIMIT] Daily cap reached. Skipping.")
            message_queue.task_done()
            continue

        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        print(f"[Reply] Waiting {delay:.0f}s to reply to {message.author}...")
        await asyncio.sleep(delay)

        reply = random.choice(REPLIES)
        typing_time = min(len(reply) * 0.05, 3.0)

        async with message.channel.typing():
            await asyncio.sleep(typing_time)

        try:
            await message.reply(reply)
            daily_count += 1
            print(f"[{daily_count}/{DAILY_LIMIT}] Replied to {message.author}: {reply}")
        except Exception as e:
            print(f"[Send error] {e}")

        await asyncio.sleep(COOLDOWN)
        message_queue.task_done()

# ── PROACTIVE LOOP ────────────────────────────────────────

async def proactive_loop():
    global daily_count, last_activity_at

    await client.wait_until_ready()
    await asyncio.sleep(30)

    while True:
        await asyncio.sleep(15)

        if not can_send():
            await asyncio.sleep(60)
            continue

        # Don't go proactive if there are still tagged messages to process
        if not message_queue.empty():
            continue

        idle_for = time.monotonic() - last_activity_at
        if idle_for < IDLE_THRESHOLD:
            continue

        guild = get_monitored_guild()
        if not guild:
            print("[Proactive] Server not found. Check MONITORED_SERVER id.")
            await asyncio.sleep(60)
            continue

        member  = pick_random_member(guild)
        channel = get_proactive_channel(guild)

        if not member:
            print("[Proactive] No valid member found.")
            await asyncio.sleep(60)
            continue

        if not channel:
            print("[Proactive] Channel not found. Check PROACTIVE_CHANNEL id.")
            await asyncio.sleep(60)
            continue

        msg   = random.choice(PROACTIVE_MESSAGES).replace("{name}", member.display_name)
        delay = random.uniform(10, 45)
        print(f"[Proactive] Idle {idle_for:.0f}s — messaging {member} in #{channel} in {delay:.0f}s")
        await asyncio.sleep(delay)

        async with channel.typing():
            await asyncio.sleep(min(len(msg) * 0.05, 2.5))

        try:
            await channel.send(f"{member.mention} {msg}")
            daily_count     += 1
            last_activity_at = time.monotonic()
            already_messaged.add(member.id)
            print(f"[{daily_count}/{DAILY_LIMIT}] Proactive → {member}: {msg}")
        except Exception as e:
            print(f"[Proactive error] {e}")

        await asyncio.sleep(COOLDOWN)

# ── EVENTS ────────────────────────────────────────────────

@client.event
async def on_ready():
    global last_activity_at
    last_activity_at = time.monotonic()
    guild = get_monitored_guild()
    print(f"✅ Logged in as {client.user}")
    print(f"Monitoring server : {guild.name if guild else '❌ NOT FOUND — check MONITORED_SERVER'}")
    print(f"Proactive channel : {guild.get_channel(PROACTIVE_CHANNEL) if guild else '❌'}")
    print(f"Members visible   : {len(guild.members) if guild else 0}")
    print(f"Daily limit       : {DAILY_LIMIT}")
    print(f"Reply delay       : {MIN_DELAY}–{MAX_DELAY}s | Cooldown: {COOLDOWN}s")
    print(f"Idle trigger      : {IDLE_THRESHOLD}s → proactive message\n")
    asyncio.create_task(process_queue())
    asyncio.create_task(proactive_loop())

@client.event
async def on_message(message):
    global last_activity_at

    # ignore own messages
    if message.author == client.user:
        return
    # ignore bots
    if message.author.bot:
        return
    # ignore DMs
    if message.guild is None:
        return
    # ignore other servers
    if message.guild.id != MONITORED_SERVER:
        return
    # ignore empty
    if not message.content.strip():
        return

    # check if tagged or replied to
    tagged = (
        client.user in message.mentions
        or (
            message.reference
            and message.reference.resolved
            and hasattr(message.reference.resolved, "author")
            and message.reference.resolved.author == client.user
        )
    )

    # Reset idle timer on ANY message in the server — not just tags
    last_activity_at = time.monotonic()

    if tagged:
        print(f"[Tagged] {message.author} in #{message.channel}: {message.content[:80]}")
        if can_send():
            await message_queue.put(message)
        else:
            print("[LIMIT] Daily cap hit.")

# ── RUN ───────────────────────────────────────────────────

if not TOKEN:
    print("ERROR: DISCORD_USER_TOKEN not set in .env")
    raise SystemExit(1)

if MONITORED_SERVER == 0:
    print("ERROR: Set your MONITORED_SERVER id at the top of the file")
    raise SystemExit(1)

if PROACTIVE_CHANNEL == 0:
    print("ERROR: Set your PROACTIVE_CHANNEL id at the top of the file")
    raise SystemExit(1)

print("Starting autotext bot...")
client.run(TOKEN)