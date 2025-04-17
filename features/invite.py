# features/invite.py

from features.invite_helpers import parse_invite_command
import logging



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
