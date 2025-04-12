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

    # 👤 Stelle sicher, dass der Benutzername im Speicher aktualisiert wird
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

    # Eingabe verarbeiten
    response = process_input(user_input, username=user_id, display_name=display_name)

    if response:
        await message.channel.send(response)

    user_memory = memory["users"].get(user_id)
    if not user_memory:
        return

    session = user_memory.get("session_state", {})

    if response and session.get("last_skill", {}).get("name") in ["!invite", "!silentinvite"]:
        try:
            guild = message.guild
            target_names = session["last_skill"]["invited"]
            message_text = session["last_skill"]["message"]
            silent = session["last_skill"]["mode"] == "silent"

            # 📢 Hole Voice-Channel des Absenders
            if message.author.voice and message.author.voice.channel:
                invite = await message.author.voice.channel.create_invite(max_age=600)
                invite_url = invite.url
            else:
                invite_url = None
                await message.channel.send("⚠️ Du musst dich in einem Voice-Channel befinden, um eine Einladung zu erstellen.")

            members = []
            for name in target_names:
                member = get(guild.members, id=int(name)) if name.isdigit() else None
                if not member:
                    member = next((m for m in guild.members if m.display_name.lower() == name.lower()), None)
                if member:
                    members.append(member)
                else:
                    print(f"⚠️ Mitglied '{name}' nicht gefunden.")

            if invite_url:
                for member in members:
                    try:
                        await member.send(f"{message_text}\n\n🔗 Hier ist dein Einladungslink: {invite_url}")
                    except Exception as e:
                        print(f"⚠️ DM an {member.display_name} fehlgeschlagen: {e}")

                if not silent:
                    await message.channel.send(f"📬 Einladung verschickt an: {', '.join(m.display_name for m in members)}")

        except Exception as e:
            print(f"❌ Fehler beim Einladungsversand: {e}")

        finally:
            session.pop("last_skill", None)

    # 🔐 Speicher zurückschreiben
    with open("memory.json", "w") as f:
        import json
        json.dump(memory, f, indent=4)

TOKEN = os.getenv("DISCORD_TOKEN")
client.run(TOKEN)
