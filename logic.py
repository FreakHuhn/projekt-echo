import json
from datetime import datetime
from gpt import get_gpt_response as gpt_call
from quiz import generiere_quizfrage, pruefe_antwort
from invite import parse_invite_command

MEMORY_FILE = "memory.json"

def load_memory():
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

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

def get_gpt_response(user_input, user_memory):
    return gpt_call(user_input, user_memory)

def process_input(user_input, username="default", display_name=None):
    memory = load_memory()
    if "users" not in memory:
        memory["users"] = {}
    if username not in memory["users"]:
        memory["users"][username] = {
            "name": display_name or username,
            "mood": "neutral",
            "session_state": {},
            "history": []
        }
    user_memory = memory["users"][username]
    text = user_input.strip()
    if not text.startswith("!"):
        return None
    log_message(user_memory, "user", user_input, username, user_memory.get("name"))
    response = handle_command(text, user_memory, username)
    log_message(user_memory, "echo", response)
    save_memory(memory)
    return response

def handle_command(command, user_memory, username):
    session = user_memory.setdefault("session_state", {})
    if command.split()[0] not in ["!invite", "!silentinvite"]:
        session.pop("last_skill", None)
    passive_commands = ["!help", "!info", "!status", "!history"]
    if command not in passive_commands:
        session["letzter_befehl"] = command
        session["modus"] = "befehl"
    print(f"🔧 handle_command: {command} von {username}")

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
            "- !gamequiz cancel: Bricht ein aktives Quiz ab\n"
            "- !antwort A/B/C/D: Antwortet auf aktive Quizfrage\n"
            "- !invite \"Benutzer1\" \"Benutzer2\" : Nachricht → Öffentliche Einladung per DM\n"
            "- !silentinvite \"Benutzer1\" ... : Nachricht → Stille Einladung ohne Channel-Output"
        )

    elif command == "!gamequiz cancel":
        session["quiz_aktiv"] = False
        session["quiz"] = {}
        session["quiz_antworten"] = {}
        session["modus"] = "neutral"
        print(f"🚫 Quizabbruch erkannt von {username}")
        return "🚫 Das aktuelle Quiz wurde abgebrochen."

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
        print(f"🎮 Quiz gestartet für Thema: {thema} – Spieler: {session['quiz_players']}")
        return (
            f"🎮 Gamequiz gestartet zum Thema: {thema}\n\n"
            f"{frage_daten['frage']}\n" +
            "\n".join(frage_daten["optionen"]) +
            "\n\nAntworte mit `!antwort A/B/C/D`"
        )

    elif command.startswith("!antwort"):
        antwort = command.split(" ", 1)[1].strip().upper() if " " in command else ""
        if not session.get("quiz_aktiv"):
            return "⚠️ Kein aktives Quiz! Starte eins mit `!gamequiz`."
        if username in session.get("quiz_antworten", {}):
            return "⏳ Du hast schon geantwortet. Warte auf die anderen."
        session.setdefault("quiz_antworten", {})[username] = antwort
        korrekt = pruefe_antwort(antwort, session)
        name = user_memory.get("name", username)
        feedback = f"{'✅ Richtig' if korrekt else '❌ Leider falsch'}, {name}."
        antworten = session.get("quiz_antworten", {})
        spieler = session.get("quiz_players", [])
        if spieler and all(uid in antworten for uid in spieler):
            session["quiz_aktiv"] = False
            session["modus"] = "neutral"
            feedback += "\nAlle haben geantwortet – das Quiz ist beendet."
        return feedback
