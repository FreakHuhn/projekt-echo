import discord
import os
from logic import process_input, load_memory
from invite import send_voice_invites
from discord.utils import get

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Echo ist eingeloggt als {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_input = message.content
    user_id = str(message.author.id)
    display_name = message.author.display_name

    memory = load_memory()
    if "users" not in memory:
        memory["users"] = {}
    if user_id not in memory["users"]:
        memory["users"][user_id] = {
            "name": display_name,
            "mood": "neutral",
            "session_state": {},
            "history": []
        }
    elif "name" not in memory["users"][user_id] or memory["users"][user_id]["name"] != display_name:
        memory["users"][user_id]["name"] = display_name

    response = process_input(user_input, username=user_id, display_name=display_name)
    print("🧪 Ergebnis von process_input():", response)

    if response and response.startswith("__ECHOLIVE__"):
        context = await build_context_from_channel(message.channel)
        print("📋 Kontext an GPT:\n", context)

        from gpt import get_live_channel_response
        gpt_response = get_live_channel_response(context)

        print("📥 GPT hat geantwortet:\n", gpt_response)
        await message.channel.send(gpt_response)
        return


    if response:
        await message.channel.send(response)

    # 🔄 Speicher neu laden, weil process_input Änderungen gemacht haben könnte
    memory = load_memory()
    user_memory = memory["users"].get(user_id)

    if not user_memory:
        return

    session = user_memory.get("session_state", {})

    # 🔒 Nur wenn Invite aktiv gesetzt wurde
    if not response or not session.get("last_skill") or session["last_skill"].get("name") not in ["!invite", "!silentinvite"]:
        return

    guild = message.guild
    target_names = session["last_skill"]["invited"]
    message_text = session["last_skill"]["message"]
    silent = session["last_skill"]["mode"] == "silent"

    try:
        if message.author.voice and message.author.voice.channel:
            invite = await message.author.voice.channel.create_invite(max_age=600)
            invite_url = invite.url
            print(f"🔗 Einladungslink erzeugt: {invite_url}")
        else:
            await message.channel.send("⚠️ Du musst dich in einem Voice-Channel befinden, um eine Einladung zu erstellen.")
            print("⚠️ Kein Voice-Channel erkannt.")
            session.pop("last_skill", None)
            return

        members = []
        for name in target_names:
            member = get(guild.members, id=int(name)) if name.isdigit() else None
            if not member:
                member = next((m for m in guild.members if m.display_name.lower() == name.lower()), None)
            if member:
                members.append(member)
            else:
                print(f"⚠️ Mitglied '{name}' nicht gefunden.")

        if not members:
            await message.channel.send("⚠️ Keine gültigen Mitglieder für die Einladung gefunden.")
            session.pop("last_skill", None)
            return

        for member in members:
            try:
                await member.send(f"{message_text}\n\n🔗 Hier ist dein Einladungslink: {invite_url}")
                print(f"✅ DM an {member.display_name} gesendet.")
            except Exception as e:
                print(f"❌ Fehler beim Senden an {member.display_name}: {e}")
                await message.channel.send(f"❌ Konnte Einladung an {member.display_name} nicht senden.")

        if not silent:
            await message.channel.send(f"📬 Einladung verschickt an: {', '.join(m.display_name for m in members)}")

    except Exception as e:
        print(f"❌ Fehler beim Einladungsversand: {e}")

    finally:
        session.pop("last_skill", None)

async def build_context_from_channel(channel, limit=10):
    # Holt die letzten X Nachrichten
    try:
        messages = await channel.history(limit=limit).flatten()
    except AttributeError:
        # fallback, falls flatten() deprecated ist (neue discord.py-Version)
        messages = []
        async for msg in channel.history(limit=limit):
            messages.append(msg)

    messages.reverse()  # älteste zuerst

    context = []
    for msg in messages:
        name = msg.author.display_name
        content = msg.content
        context.append(f"{name}: {content}")

    return "\n".join(context)

TOKEN = os.getenv("DISCORD_TOKEN")
client.run(TOKEN)
