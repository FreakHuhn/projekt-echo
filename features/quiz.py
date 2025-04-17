# features/quiz.py

import re
import random
from datetime import datetime
from features.quiz_helpers import generiere_quizfrage, versuche_warhammer_easteregg, bewerte_antwort


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
        frage_daten = generiere_quizfrage(user_memory, thema)

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