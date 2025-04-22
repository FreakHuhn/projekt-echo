# features/quiz.py

import re
import random
from datetime import datetime
from gpt import generate_quiz_question


# 🧠 Hauptfunktion: verarbeitet quiz-bezogene Befehle (!gamequiz, !antwort)
def handle_quiz_command(command, user_memory, username):
    session = user_memory.setdefault("session_state", {})

    # 🧩 Wenn der Befehl ein Quiz starten soll
    if command.startswith("!gamequiz"):
        # 1. Spieler extrahieren (Mentions in Discord-Format) und Thema
        mention_ids = re.findall(r'<@!?(\d+)>', command)
        thema_match = re.search(r'"([^"]+)"', command)
        thema = thema_match.group(1) if thema_match else "Allgemein"

        # 2. Spieler-Liste zusammenstellen (du selbst + erwähnte Mitspieler)
        quiz_players = list(set([username] + mention_ids))

        # 3. Warhammer Easteregg prüfen (seltene Sonderfrage)
        spezialquiz = versuche_warhammer_easteregg(thema)
        if spezialquiz:
            session["quiz"] = {
                "frage": spezialquiz["frage"],
                "optionen": spezialquiz["optionen"],
                "lösung": spezialquiz["lösung"]
            }
            session["quiz_startzeit"] = spezialquiz["startzeit"]
            session["quiz_aktiv"] = True
            session["modus"] = "quiz"
            session["quiz_players"] = quiz_players
            session["quiz_antworten"] = {}

            frage_text = spezialquiz["frage"]
            optionen_text = "\n".join(spezialquiz["optionen"])

            return (
                f"💀 *Sonderfall erkannt: For the Emperor!*\n\n"
                f"{frage_text}\n{optionen_text}\n\n"
                f"Antwortet mit `!antwort A/B/C/D` – nur 10 Sekunden Zeit!"
            )

        # 4. Normale GPT-Frage generieren
        antwort_rohtext = generate_quiz_question(thema)
        frage_daten = parse_quizantwort(antwort_rohtext)


        # 5. Session vorbereiten
        session["quiz"] = frage_daten
        session["quiz_aktiv"] = True
        session["modus"] = "quiz"
        session["quiz_players"] = quiz_players
        session["quiz_antworten"] = {}

        frage_text = frage_daten["frage"]
        optionen_text = "\n".join(frage_daten["optionen"])

        # 6. Rückmeldung je nach Spieleranzahl
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

        # ⏳ Der !antwort-Teil kommt als nächstes...

    # 🧩 Spieler antwortet auf eine Quizfrage
    elif command.startswith("!antwort"):
        antwort = command.split(" ", 1)[1].strip().upper() if " " in command else ""

        if not session.get("quiz_aktiv"):
            return "⚠️ Kein aktives Quiz! Starte eins mit `!gamequiz`."

        antworten = session.setdefault("quiz_antworten", {})
        spieler = session.get("quiz_players", [])

        if username in antworten:
            return "⏳ Du hast schon geantwortet. Warte auf die anderen."

        antworten[username] = antwort
        verbleibend = [uid for uid in spieler if uid not in antworten]

        if verbleibend:
            return (
                f"✅ Antwort gespeichert für <@{username}>.\n"
                f"⏳ Noch ausstehend: {', '.join([f'<@{uid}>' for uid in verbleibend])}"
            )

        # 🧠 Alle haben geantwortet → auswerten
        frage_info = session.get("quiz", {})
        auswertung = []

        for uid in spieler:
            user_antwort = antworten.get(uid, "—")
            result = bewerte_antwort(user_antwort, session, uid)

            if result["grund"] == "timeout":
                text = f"<@{uid}>: {user_antwort} ⛔️ Too late, Heretic."
            elif result["korrekt"]:
                text = f"<@{uid}>: {user_antwort} ✅"
            else:
                text = f"<@{uid}>: {user_antwort} ❌"

            auswertung.append(text)

        session["quiz_aktiv"] = False
        session["modus"] = "neutral"

        return (
            f"📊 Alle Antworten sind eingegangen! Die richtige Lösung war: **{frage_info.get('lösung', '?')}**\n\n"
            + "\n".join(auswertung)
        )
    return "Unbekannter Quiz-Befehl."

# 🔧 Hilfsfunktionen (vormals aus quiz_helpers.py)

# 🔍 Zerlegt den GPT-Rohtext in ein Dictionary mit Frage, Antwortoptionen und Lösung
def parse_quizantwort(text):
    lines = text.strip().splitlines()
    frage = ""
    optionen = []
    loesung = "?"

    for line in lines:
        if line.lower().startswith(("frage:", "question:")):
            frage = line.split(":", 1)[1].strip()
        elif line.strip().startswith(("A)", "B)", "C)", "D)")):
            optionen.append(line.strip())
        elif any(key in line.lower() for key in ["richtige antwort", "correct answer"]):
            rohausgabe = line.split(":")[-1].strip().upper()
            loesung = re.sub(r"[^A-D]", "", rohausgabe)  # Nur A–D zulassen

    return {
        "frage": frage,
        "optionen": optionen,
        "lösung": loesung
    }


# 💀 Warhammer Easter Egg – Spezialmodus bei Thema "Warhammer"
def versuche_warhammer_easteregg(thema):
    if thema.lower() != "warhammer":
        return None

    if random.random() <= 0.1:
        print("💀 Warhammer Easter Egg aktiviert.")  # Debug-Ausgabe

        frage = "For the ...?"
        optionen = [
            "A) Emperor!",
            "B) Emperor!",
            "C) Emperor!",
            "D) Emperor!"
        ]
        return {
            "frage": frage,
            "optionen": optionen,
            "lösung": "ALLE",  # Spezialfall – alle gelten, aber mit Zeitlimit
            "startzeit": datetime.now().isoformat()
        }

    return None


# ✅ Bewertet eine Quiz-Antwort inkl. Spezialfälle (ALLE, Timeout etc.)
def bewerte_antwort(antwort, session, user_id):
    frage = session.get("quiz", {})
    loesung = frage.get("lösung", "?")
    startzeit = frage.get("startzeit") or session.get("quiz_startzeit")
    antwort = antwort.strip().upper()

    if loesung == "ALLE":
        if startzeit:
            start_dt = datetime.fromisoformat(startzeit)
            zeit_differenz = (datetime.now() - start_dt).total_seconds()
            if zeit_differenz > 10:
                return {
                    "korrekt": False,
                    "grund": "timeout",
                    "antwort": antwort,
                    "richtig": "ALLE"
                }
        return {
            "korrekt": True,
            "grund": "richtig",
            "antwort": antwort,
            "richtig": "ALLE"
        }

    korrekt = antwort == loesung
    return {
        "korrekt": korrekt,
        "grund": "richtig" if korrekt else "falsch",
        "antwort": antwort,
        "richtig": loesung
    }
