# features/invite.py
import logging
import re
import discord




# 📬 Verarbeitet !invite und !silentinvite Befehle
def handle_invite_command(command, user_memory, username):
    usernames, nachricht = parse_invite_command(command, sender_name=user_memory.get("name", username))
    if not usernames:
        return nachricht

    session = user_memory.setdefault("session_state", {})
    session["last_skill"] = {
        "name": command.split()[0],  # "!invite" oder "!silentinvite"
        "invited": usernames,
        "message": nachricht,
        "mode": "silent" if command.startswith("!silent") else "public"
    }

    sichtbarkeit = "stille" if session["last_skill"]["mode"] == "silent" else "öffentliche"
    zeile_pro_user = "\n".join([f"📨 Einladung an {name} erkannt (noch nicht verschickt)." for name in usernames])
    return f"{zeile_pro_user}\n({sichtbarkeit.capitalize()} Einladung wird vorbereitet)"

    # Diese Funktion parst Befehle wie:
    # !invite "User1" "User2": Nachricht
    # und trennt Namen von der Nachricht hinter dem Doppelpunkt
    # Neuer parse_invite, hoffentlich mit anzeige wer die Einladung verschickt hat.
def parse_invite_command(command, sender_name="Jemand"):
    if ':' in command:
        vor_dem_doppelpunkt, nachricht_roh = command.split(':', 1)
    else:
        vor_dem_doppelpunkt = command
        nachricht_roh = ""

    parts = re.findall(r'"([^\"]+)"|<@!?([0-9]+)>', vor_dem_doppelpunkt)
    usernames = []

    for name, mention in parts:
        if mention:
            usernames.append(mention)
        elif name:
            usernames.append(name.strip())

    if not usernames:
        return None, "❌ Kein gültiger Benutzer erkannt."

    # ⬇️ Neue Nachricht mit personalisiertem Standardtext
    if nachricht_roh.strip():
        nachricht = nachricht_roh.strip()
    else:
        nachricht = f"Hey, {sender_name} hat dich in seinen Channel zum Quatschen eingeladen."

    return usernames, nachricht


# Diese Funktion sendet Voice-Einladungen per DM an Discord-Nutzer
# ctx.channel.send(...) wird nur verwendet, wenn 'silent' = False

async def send_voice_invites(ctx, members, message_text, silent=False):
    confirmations = []

    for member in members:
        try:
            await member.send(message_text)
            confirmations.append(member.display_name)
        except Exception as e:
            print(f"⚠️ Konnte Nachricht an {member.display_name} nicht senden: {e}")

    if not silent and confirmations:
        await ctx.channel.send(f"Einladungen verschickt an: {', '.join(confirmations)}")

