import json
from datetime import datetime
from gpt import get_gpt_response as gpt_call
from features.quiz import handle_quiz_command
from features.invite import handle_invite_command
from gpt import handle_echo_command
from gpt import handle_echolive_command
from gpt import handle_judge_command
from features.memory_io import load_memory, save_memory





MEMORY_FILE = "memory.json"

# 🔁 Lädt das Memory-File

def load_memory():
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

# 💾 Speichert das Memory-File

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

# 📝 Fügt Eintrag in History ein (User oder Echo)

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

# 🧠 GPT-Wrapper – ermöglicht system_prompt-Personalisierung

def get_gpt_response(user_input, user_memory, use_persona=True):
    return gpt_call(user_input, user_memory, use_persona=use_persona)

# 🔄 Hauptverarbeitung pro Nachricht

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
    response, should_log = handle_command(text, user_memory, username)
    if should_log:
        log_message(user_memory, "echo", response)
        save_memory(memory)
    return response

# 💬 Befehlsverarbeitung

def handle_command(command, user_memory, username) -> tuple[str, bool]:
    session = user_memory.setdefault("session_state", {})

    # passive Befehle werden nicht als letzter Befehl gespeichert
    passive_commands = ["!help", "!status", "!history"]
    # last_skill wird nur gelöscht, wenn kein Invite-Befehl vorliegt
    if command.split()[0] not in ["!invite", "!silentinvite"]:
        session.pop("last_skill", None)
    # nur aktive Befehle setzen letzten Befehl und Modus
    if command not in passive_commands:
        session["letzter_befehl"] = command
        session["modus"] = "befehl"

    print(f"🔧 handle_command: {command} von {username}")

    # listet alle verfügbaren Befehle mit kurzer Beschreibung
    if command == "!help":
        return (
            "📖 **Verfügbare Befehle:**\n"
            "- `!antwort A/B/C/D` – Antwort auf aktive Quizfrage\n"
            "- `!echo <Text>` – Fragt Echo direkt (GPT mit Persönlichkeit)\n"
            "- `!echolive` – Echo kommentiert den aktuellen Chatverlauf\n"
            "- `!gamequiz \"Thema\" [@User1 @User2]` – Startet ein Nerd-Quiz\n"
            "- `!gamequiz cancel` – Bricht ein aktives Quiz ab\n"
            "- `!help` – Zeigt diese Übersicht\n"
            "- `!history` – Zeigt die letzten 5 Nachrichten\n"
            "- `!invite \"Name1\" \"Name2\" : Text` – Öffentliche Einladungen per DM\n"
            "- `!judge [@User]` – Echo urteilt gnadenlos über den Channel (oder eine Person)\n"
            "- `!reset` – Setzt deinen Session-Zustand und Verlauf zurück\n"
            "- `!silentinvite \"Name1\" ... : Text` – Stille Einladungen (nur per DM)\n"
            "- `!status` – Zeigt deinen aktuellen Zustand\n"
            "- `!tip <Thema>` – Kurzer Tipp von Echo"
            ), False

   
    # zeigt aktuellen Zustand des Users: Name, Stimmung, Modus, letzter Befehl
    elif command == "!status":
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
        ), False
    
    # setzt Stimmung, Verlauf und Session-State des Nutzers zurück
    elif command == "!reset":
        name = user_memory.get("name", username)
        user_memory["mood"] = "neutral"
        user_memory["session_state"] = {}
        user_memory["history"] = []
        return f"🔄 Alles zurückgesetzt für {name}. Frischer Start – los geht's!", False

    # generiert kurzen Tipp zum angegebenen Thema (noch ohne Persona-Stil)
    elif command.startswith("!tip"):
        teile = command.split(" ", 1)
        thema = teile[1] if len(teile) > 1 else "unbestimmt"
        prompt = (
            f"Gib mir einen kurzen, motivierenden oder hilfreichen Tipp für das Thema '{thema}'. "
            f"Halte dich kurz, sei pragmatisch, etwas trocken und leicht humorvoll."
        )
        response = get_gpt_response(prompt, user_memory, use_persona=False)
        return f"💡 Tipp zum Thema *{thema}*:\n{response}", False

    # zeigt die letzten fünf Nachrichten (User + Echo) mit Zeitstempel
    elif command == "!history":
        history = user_memory.get("history", [])
        last_entries = history[-5:]
        lines = []
        for entry in last_entries:
            wer = "🧍" if entry["speaker"] == "user" else "🤖"
            zeit = entry.get("timestamp", "?")
            text = entry.get("message", "")
            lines.append(f"{wer} [{zeit}]: {text}")
        return "\n".join(lines),False

    # bricht ein aktives Quiz ab und leert zugehörige Session-Einträge
    elif command == "!gamequiz cancel":
        session["quiz_aktiv"] = False
        session["quiz"] = {}
        session["quiz_antworten"] = {}
        session["modus"] = "neutral"
        print(f"🚫 Quizabbruch erkannt von {username}")
        return "🚫 Das aktuelle Quiz wurde abgebrochen.",False

    # leitet User-Eingabe an GPT weiter (mit Persona), wenn !echo verwendet wird
    elif command.startswith("!echo"):
        antwort = handle_echo_command(command, user_memory, username)
        return antwort, True

    # startet ein GPT-generiertes Quiz zum Thema mit optionalen Mitspielern(Multiplayer funktion in Arbeit, soweit aber schon Funktionsfähig. BRAUCHT TESTUNG!)
    elif command.startswith("!gamequiz") or command.startswith("!antwort"):
        antwort = handle_quiz_command(command, user_memory, username)
        return antwort, True
    
    elif command.startswith("!invite") or command.startswith("!silentinvite"):
        antwort = handle_invite_command(command, user_memory, username)
        return antwort, True

    elif command.startswith("!echolive"):
        return handle_echolive_command(command, user_memory, username), False


    elif command.startswith("!judge"):
        return handle_judge_command(command, user_memory, username), False

    return "Unbekannter Befehl. Gib `!help` ein für alle Befehle.", False
