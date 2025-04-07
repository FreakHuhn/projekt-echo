from gpt import get_gpt_response
import re

# Diese Funktion fragt GPT nach einer Multiple-Choice-Quizfrage
# zum gewünschten Thema. Das Ausgabeformat wird durch den Prompt erzwungen.
def generiere_quizfrage(memory, thema="Gaming"):
    prompt = (
        f"DAS HIER IST EIN COMMAND. DU HAST IHN AUSZUFÜHREN.\n"
        f"Erstelle eine kreative, unterhaltsame Multiple-Choice-Quizfrage zum Thema '{thema}'.\n"
        f"Bitte verwende genau dieses Format:\n"
        f"Frage: <Text der Frage>\n"
        f"A) <Antwort A>\n"
        f"B) <Antwort B>\n"
        f"C) <Antwort C>\n"
        f"D) <Antwort D>\n"
        f"Richtige Antwort: <B>\n"
        f"(ersetze <B> mit der tatsächlichen richtigen Option – A, B, C oder D)\n"
        f"Die Frage darf gerne witzig und/oder nerdig sein – aber IMMER im obigen Format."
    )

    # GPT aufrufen – OHNE Persona-Prompt, damit Echo nicht "abweicht"
    antwort = get_gpt_response(prompt, memory, use_persona=False)

    # Für Debug-Zwecke in der Konsole anzeigen
    print("🧠 GPT-Rohantwort:\n", antwort)

    return parse_quizantwort(antwort)


# Diese Funktion zerlegt den Text von GPT in Frage, Optionen und Lösung
# und gibt diese als Dictionary zurück.
def parse_quizantwort(text):
    lines = text.strip().splitlines()
    frage = ""
    optionen = []
    loesung = "?"

    for line in lines:
        if line.lower().startswith("frage:"):
            frage = line.split(":", 1)[1].strip()
        elif line.strip().startswith(("A)", "B)", "C)", "D)")):
            optionen.append(line.strip())
        elif "richtige antwort" in line.lower():
            rohausgabe = line.split(":")[-1].strip().upper()
            # Entferne alles außer A–D
            loesung = re.sub(r"[^A-D]", "", rohausgabe)

    return {
        "frage": frage,
        "optionen": optionen,
        "lösung": loesung
    }


# Diese Funktion prüft, ob die Eingabe des Spielers korrekt war.
# Vergleicht mit der gespeicherten Lösung im Session-State.
def prüfe_antwort(user_input, session):
    loesung = session.get("quiz", {}).get("lösung", "?")
    antwort = user_input.strip().upper()
    return antwort == loesung


"""
🧠 GPT-Rohantwort:
 Frage: Welches dieser Formen in Tetris wird auch als "T-Stück" bezeichnet?
A) Quadrat
B) L-Stück
C) Z-Stück
D) T-Stück
Richtige Antwort: D

BRUH was das für ne frage
"""
