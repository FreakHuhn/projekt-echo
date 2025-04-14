import json
from datetime import datetime
from gpt import get_gpt_response as gpt_call
from quiz import generiere_quizfrage, prüfe_antwort
from invite import parse_invite_command  # Jetzt mit neuer Parser-Logik

MEMORY_FILE = "memory.json"

# Gedächtnis laden
def load_memory():
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

# Gedächtnis speichern
def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

# Nachricht in History eintragen mit ID & Name
def log_message(user_memory, speaker, message, user_id=None, user_name=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "speaker": speaker,
        "message": message,
        "timestamp": timestamp
    }
    if speaker == "user":
        entry["user_id"] = user_id
        entry["user_name"] = user_name

    user_memory.setdefault("history", []).append(entry)

# GPT-Antwort erzeugen (Hülle für den Import)
def get_gpt_response(user_input, user_memory):
    return gpt_call(user_input, user_memory)

# Hauptverarbeitung

def process_input(user_input, username="default", display_name=None):
    memory = load_memory()

    if "users" not in memory:
        memory["users"] = {}

    if username not in memory["users"]:
        # ⬇️ Name beim ersten Kontakt speichern
        memory["users"][username] = {
            "name": display_name or username,
            "mood": "neutral",
            "session_state": {},
            "history": []
        }

    user_memory = memory["users"][username]

    text = user_input.strip()

    # ❗ Sicherheitscheck: Nur auf echte Commands reagieren
    if not text.startswith("!"):
        return None  # Ignorieren ohne Reaktion

    log_message(user_memory, "user", user_input, username, user_memory.get("name"))
    response = handle_command(text, user_memory, username)
    log_message(user_memory, "echo", response)

    save_memory(memory)
    return response

# Kommandos verarbeiten

def handle_command(command, user_memory, username):
    session = user_memory.setdefault("session_state", {})
    
    # ⛔️ Invite-Rückstand wegräumen, wenn kein neuer Invite-Befehl kommt
    if command.split()[0] not in ["!invite", "!silentinvite"]:
        session.pop("last_skill", None)
    
    # ❌ Passive Commands sollen nicht als letzter Befehl gelten
    passive_commands = ["!help", "!info", "!status", "!history"]
    if command not in passive_commands:
        session["letzter_befehl"] = command
        session["modus"] = "befehl"

    print(f"🔧 handle_command: {command} von {username}")  # Debug-Ausgabe

    if command == "!help":
        return (
            "📖 Verfügbare Befehle:\n"
            "- !help: Zeigt diese Übersicht\n"
            "- !info: Zeigt Name und Stimmung\n"
            "- !history: Zeigt die letzten 5 Einträge\n"
            "- !status: Zeigt den aktuellen Systemzustand\n"
            "- !tip \"Thema\": Gibt einen kurzen Hinweis\n"
            "- !echo <Text>: Fragt Echo direkt (GPT)\n"
            "- !gamequiz \"Thema\" @User1 @User2 ...: Startet ein Quiz (optional Multiplayer)\n"
            "- !antwort A/B/C/D: Antwortet auf aktive Quizfrage\n"
            "- !invite \"Benutzer1\" \"Benutzer2\" : Nachricht → Öffentliche Einladung per DM\n"
            "- !silentinvite \"Benutzer1\" ... : Nachricht → Stille Einladung ohne Channel-Output"
        )

    elif command == "!info":
        name = user_memory.get("name", "unbekannt")
        mood = user_memory.get("mood", "neutral")
        return f"Name: {name}\nStimmung: {mood}"

    elif command.startswith("!echo"):
        user_input = command[len("!echo"):].strip()
        if not user_input:
            return "Was soll ich denn wiederholen, hm?"
        response = gpt_call(user_input, user_memory, use_persona=True)
        session["modus"] = "gpt"
        return response

    elif command == "!history":
        history = user_memory.get("history", [])
        last_entries = history[-5:]
        lines = []
        for entry in last_entries:
            who = "🧍" if entry["speaker"] == "user" else "🤖"
            lines.append(f"{who} [{entry['timestamp']}]: {entry['message']}")
        return "\n".join(lines)

    elif command == "!status":
        session = user_memory.get("session_state", {})
        name = user_memory.get("name", "unbekannt")
        mood = user_memory.get("mood", "neutral")
        modus = session.get("modus", "unbekannt")
        letzter_befehl = session.get("letzter_befehl", "unbekannt")
        return (
            f"🧠 Aktueller Status:\n"
            f"- Benutzer: {name}\n"
            f"- Stimmung: {mood}\n"
            f"- Modus: {modus}\n"
            f"- Letzter Befehl: {letzter_befehl}"
        )

    elif command.startswith("!tip"):
        teile = command.split(" ", 1)
        thema = teile[1] if len(teile) > 1 else "unbestimmt"
        prompt = (
            f"Gib mir einen kurzen, motivierenden oder hilfreichen Tipp für das Thema '{thema}'. "
            f"Halte dich kurz, sei pragmatisch, etwas trocken und leicht humorvoll."
        )
        response = gpt_call(prompt, user_memory, use_persona=False)
        return f"💡 Tipp zum Thema *{thema}*:{response}"

    elif command.startswith("!gamequiz"):
        teile = command.split(" ", 1)
        args = teile[1] if len(teile) > 1 else ""

        import re
        thema_match = re.search(r'"([^\"]+)"', args)
        mentions = re.findall(r'<@!?([0-9]+)>', args)

        thema = thema_match.group(1) if thema_match else "Gaming"
        frage_daten = generiere_quizfrage(user_memory, thema)

        session["quiz"] = frage_daten
        session["quiz_aktiv"] = True
        session["modus"] = "quiz"

        session["quiz_players"] = [username] + mentions
        session["quiz_antworten"] = {}

        print(f"🎮 Quiz gestartet für Thema: {thema} – Spieler: {session['quiz_players']}")  # Debug-Ausgabe

        return (
            f"🎮 Gamequiz gestartet zum Thema: {thema}\n\n"
            f"{frage_daten['frage']}\n" +
            "\n".join(frage_daten["optionen"]) +
            "\n\nAntworte mit `!antwort A/B/C/D`"
        )
    elif command == "!gamequiz cancel":
        session["quiz_aktiv"] = False
        session["quiz"] = {}
        session["quiz_antworten"] = {}
        session["modus"] = "neutral"
        return "🚫 Das aktuelle Quiz wurde abgebrochen."

    elif command.startswith("!antwort"):
        session = user_memory.get("session_state", {})
        if not session.get("quiz_aktiv"):
            return "Kein aktives Quiz! Starte eins mit `!gamequiz`."

        teile = command.split(" ")
        if len(teile) != 2:
            return "Bitte antworte mit `!antwort A/B/C/D`."
        antwort = teile[1].upper()

        session.setdefault("quiz_antworten", {})[username] = antwort

        richtige = session.get("quiz", {}).get("lösung", "?")
        spieler = session.get("quiz_players", [])
        name = user_memory.get("name", "Freund")

        korrekt = prüfe_antwort(antwort, session)
        feedback = f"✅ Richtig, {name}!" if korrekt else f"❌ Leider falsch, {name}. Richtige Antwort: {richtige}"

        print(f"📝 Antwort von {username}: {antwort} – {'✔' if korrekt else '✘'}")  # Debug-Ausgabe

        if all(uid in session["quiz_antworten"] for uid in spieler):
            session["quiz_aktiv"] = False
            session["quiz"] = {}
            return feedback + "\nAlle haben geantwortet – das Quiz ist beendet."
        else:
            return feedback + "\n(Warte noch auf andere Antworten...)"

    elif command.startswith("!invite") or command.startswith("!silentinvite"):
        usernames, nachricht = parse_invite_command(command, sender_name=user_memory.get("name", "Ein User"))
        
        if usernames is None:
            return nachricht
        output = ""
        for user in usernames:
            output += f"📬 Einladung an {user} erkannt (noch nicht verschickt).\n"
        if command.startswith("!invite"):
            output += "(öffentliche Einladung wird vorbereitet)"
        else:
            output += "(stille Einladung wird vorbereitet)"
        session["last_skill"] = {
            "name": command.split()[0],
            "invited": usernames,
            "message": nachricht,
            "mode": "silent" if command.startswith("!silentinvite") else "public"
        }
        print(f"✉️ Einladungen vorbereitet für: {usernames} – Modus: {session['last_skill']['mode']}")  # Debug
        return output

    else:
        return "Unbekannter Befehl. Gib `!help` ein für alle Befehle."
