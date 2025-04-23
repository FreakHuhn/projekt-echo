# features/profil.py
from datetime import datetime


# 📌 Erstellt ein persönliches Echo-Profil für den Nutzer
# 
# Zeigt:
# - Aktuellen Session-Zustand (Stimmung, Modus, letzter Befehl, Quiz-Aktivität)
# - Nutzungsverhalten basierend auf der Befehls-History (!echo, !tip, !gamequiz, ...)
# - Häufigster Befehl
# - Letztes Echo-Zitat aus der Historie
# 
# Idee: Mischung aus Statusübersicht und verspielter Selbstreflexion
# → Grundlage für spätere Erweiterungen wie !moodcheck oder "Echo-Titel"



# 📊 Verarbeitet !profil – Kombination aus Status, Statistik, Zitat etc.
def handle_profil_command(command, user_memory, username):
    name = user_memory.get("name", username)
    mood = user_memory.get("mood", "neutral")
    session = user_memory.get("session_state", {})

    letzter_befehl = session.get("letzter_befehl", "unbekannt")
    modus = session.get("modus", "unbekannt")
    quiz_aktiv = session.get("quiz_aktiv", False)

    history = user_memory.get("history", [])
    befehle = [entry["message"].split()[0] for entry in history if entry["speaker"] == "user" and entry["message"].startswith("!")]
    befehl_stats = {cmd: befehle.count(cmd) for cmd in set(befehle)}
    häufigster_befehl = max(befehl_stats.items(), key=lambda x: x[1])[0] if befehl_stats else "–"

    letztes_zitat = next((entry["message"] for entry in reversed(history) if entry["speaker"] == "echo"), "–")

    return (
        f"🧠 **Profil für {name}**\n"
        f"- Stimmung: {mood}\n"
        f"- Letzter Modus: {modus}\n"
        f"- Letzter Befehl: {letzter_befehl}\n"
        f"- Aktives Quiz: {'Ja' if quiz_aktiv else 'Nein'}\n\n"
        f"📊 **Nutzung**\n" +
        "\n".join([f"- {cmd}: {count}×" for cmd, count in sorted(befehl_stats.items())]) +
        f"\n- Häufigster Befehl: {häufigster_befehl}\n\n"
        f"💬 **Letztes Echo-Zitat**\n„{letztes_zitat}“"
    )


# 🧠 Verarbeitet !status separat
def handle_status_command(user_memory, username):
    session = user_memory.get("session_state", {})
    name = user_memory.get("name", username)
    mood = user_memory.get("mood", "neutral")
    modus = session.get("modus", "unbekannt")
    letzter = session.get("letzter_befehl", "unbekannt")

    return (
        f"🧠 Aktueller Status:\n"
        f"- Benutzer: {name}\n"
        f"- Stimmung: {mood}\n"
        f"- Modus: {modus}\n"
        f"- Letzter Befehl: {letzter}"
    )


# 🔄 Verarbeitet !reset separat
def handle_reset_command(user_memory, username):
    user_memory["mood"] = "neutral"
    user_memory["session_state"] = {}
    user_memory["history"] = []

    return f"🔄 Alles zurückgesetzt für {username}. Frischer Start – los geht's!"
