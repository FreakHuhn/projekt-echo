import json
from datetime import datetime
from gpt import get_gpt_response as gpt_call
from quiz import generiere_quizfrage, pruefe_antwort
from invite import parse_invite_command

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
    response = handle_command(text, user_memory, username)
    log_message(user_memory, "echo", response)
    save_memory(memory)
    return response

# 💬 Befehlsverarbeitung

def handle_command(command, user_memory, username):
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
            "📖 Verfügbare Befehle:\n"
            "- !help: Zeigt diese Übersicht\n"
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
            )
    
    # setzt Stimmung, Verlauf und Session-State des Nutzers zurück
    elif command == "!reset":
        name = user_memory.get("name", username)
        user_memory["mood"] = "neutral"
        user_memory["session_state"] = {}
        user_memory["history"] = []
        return f"🔄 Alles zurückgesetzt für {name}. Frischer Start – los geht's!"

    # generiert kurzen Tipp zum angegebenen Thema (noch ohne Persona-Stil)
    elif command.startswith("!tip"):
        teile = command.split(" ", 1)
        thema = teile[1] if len(teile) > 1 else "unbestimmt"
        prompt = (
            f"Gib mir einen kurzen, motivierenden oder hilfreichen Tipp für das Thema '{thema}'. "
            f"Halte dich kurz, sei pragmatisch, etwas trocken und leicht humorvoll."
        )
        response = get_gpt_response(prompt, user_memory, use_persona=False)
        return f"💡 Tipp zum Thema *{thema}*:\n{response}"

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
        return "\n".join(lines)

    # bricht ein aktives Quiz ab und leert zugehörige Session-Einträge
    elif command == "!gamequiz cancel":
        session["quiz_aktiv"] = False
        session["quiz"] = {}
        session["quiz_antworten"] = {}
        session["modus"] = "neutral"
        print(f"🚫 Quizabbruch erkannt von {username}")
        return "🚫 Das aktuelle Quiz wurde abgebrochen."

    # leitet User-Eingabe an GPT weiter (mit Persona), wenn !echo verwendet wird
    elif command.startswith("!echo"):
        user_input = command[len("!echo"):].strip()
        if not user_input:
            return "Was soll ich denn wiederholen, hm?"
        response = get_gpt_response(user_input, user_memory, use_persona=True)
        session["modus"] = "gpt"
        return response

    # startet ein GPT-generiertes Quiz zum Thema mit optionalen Mitspielern(Multiplayer funktion in Arbeit)
    elif command.startswith("!gamequiz"):
        import re

    # 🔍 1. Mentions (Discord-ID Format) und Thema (in Anführungszeichen) extrahieren
        mention_ids = re.findall(r'<@!?(\d+)>', command)
        thema_match = re.search(r'"([^"]+)"', command)
        thema = thema_match.group(1) if thema_match else "Allgemein"

    # 👥 2. Spieler setzen (du selbst + alle gültigen Mentions)
        quiz_players = list(set([username] + mention_ids))

    # 🧠 3. Quizfrage generieren mit GPT (bestehende Funktion)
        frage_daten = generiere_quizfrage(user_memory, thema)

    # 💾 4. Session-Setup
        session["quiz"] = frage_daten
        session["quiz_aktiv"] = True
        session["modus"] = "quiz"
        session["quiz_players"] = quiz_players
        session["quiz_antworten"] = {}

    # 📝 5. Formatierte Rückgabe (Solo vs Multiplayer)
        frage_text = frage_daten["frage"]
        optionen_text = "\n".join(frage_daten["optionen"])

        if len(quiz_players) == 1:
            return (
                f"🧠 Solo-Quiz zum Thema: *{thema}* wurde gestartet!\n\n"
                f"{frage_text}\n{optionen_text}\n\n"
                f"Antwort mit `!antwort A/B/C/D` – sofortige Auswertung nach deiner Eingabe."
        )
        else:
            mentions_text = ", ".join([f"<@{uid}>" for uid in quiz_players])
            return (
                f"🎮 Multiplayer-Quiz zum Thema: *{thema}* wurde gestartet!\n"
                f"Eingeladene Spieler: {mentions_text}\n\n"
                f"{frage_text}\n{optionen_text}\n\n"
                f"Antwortet mit `!antwort A/B/C/D` – das Ergebnis kommt, sobald alle geantwortet haben."
            )

    
    elif command.startswith("!antwort"):
        antwort = command.split(" ", 1)[1].strip().upper() if " " in command else ""

        if not session.get("quiz_aktiv"):
            return "⚠️ Kein aktives Quiz! Starte eins mit `!gamequiz`."

        antworten = session.setdefault("quiz_antworten", {})
        spieler = session.get("quiz_players", [])

        if username in antworten:
            return "⏳ Du hast schon geantwortet. Warte auf die anderen."

    # 📝 Antwort speichern, aber noch NICHT bewerten
        antworten[username] = antwort

        verbleibend = [uid for uid in spieler if uid not in antworten]

    # 👥 Wenn noch Spieler fehlen → warten
        if verbleibend:
            return (
                f"✅ Antwort gespeichert für <@{username}>.\n"
                f"⏳ Noch ausstehend: {', '.join([f'<@{uid}>' for uid in verbleibend])}"
            )

    # ✅ Alle haben geantwortet → auswerten!
        frage_info = session.get("quiz", {})
        loesung = frage_info.get("lösung", "?")

        auswertung = []
        for uid in spieler:
            gegeben = antworten.get(uid, "—")
            korrekt = "✅" if gegeben == loesung else "❌"
            auswertung.append(f"<@{uid}>: {gegeben} {korrekt}")

    # 🔒 Quiz abschließen
        session["quiz_aktiv"] = False
        session["modus"] = "neutral"

        return (
            f"📊 Alle Antworten sind eingegangen! Die richtige Lösung war: **{loesung}**\n\n"
            + "\n".join(auswertung)
        )



    elif command.startswith("!invite") or command.startswith("!silentinvite"):
        usernames, nachricht = parse_invite_command(command, sender_name=user_memory.get("name", username))
        if not usernames:
            return nachricht
        
        session["last_skill"] = {
            "name": command.split()[0],  # "!invite" oder "!silentinvite"
            "invited": usernames,
            "message": nachricht,
            "mode": "silent" if command.startswith("!silent") else "public"
            }
        sichtbarkeit = "stille" if session["last_skill"]["mode"] == "silent" else "öffentliche"
        zeile_pro_user = "\n".join([f"📨 Einladung an {name} erkannt (noch nicht verschickt)." for name in usernames])
        return f"{zeile_pro_user}\n({sichtbarkeit.capitalize()} Einladung wird vorbereitet)"
    
    return "Unbekannter Befehl. Gib `!help` ein für alle Befehle."
