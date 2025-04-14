from gpt import get_gpt_response
import re

# Diese Funktion fragt GPT nach einer Multiple-Choice-Quizfrage
# zum gewünschten Thema. Das Ausgabeformat wird durch den Prompt erzwungen.
# Zu Englischen Promtps gewechselt für hoffentlich schwierigere Fragen
def generiere_quizfrage(memory, thema="Gaming"):
    prompt = (
        f"THIS IS A COMMAND. YOU MUST EXECUTE IT.\n"
        f"You are Echo, a Discord bot. German is your native language, and you ALWAYS reply in fluent, idiomatic German.\n"
        f"Create a creative and entertaining multiple-choice quiz question about the topic: '{thema}'.\n"
        f"The question should focus on deep nerd knowledge – lore, obscure mechanics, or high-level meta.\n"
        f"NO easy-mode baby questions! The players have been gamers longer than you've been online.\n"
        f"These questions should be, exaggeratedly speaking, 500 IQ level.\n\n"
        f"Use exactly this format:\n"
        f"Frage: <Text der Frage>\n"
        f"A) <Antwort A>\n"
        f"B) <Antwort B>\n"
        f"C) <Antwort C>\n"
        f"D) <Antwort D>\n"
        f"Richtige Antwort: <B>\n"
        f"(Replace <B> with the actual correct option – A, B, C, or D)\n\n"
        f"The tone may be witty or nerdy – but the format MUST match exactly."
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
QUIZ FAILS!!!!! schon ein bisschen lustig:
🧠 GPT-Rohantwort:
 Frage: Welches Spiel wird oft als "The Legend of Zelda" bezeichnet?
A) Super Mario Bros
B) The Witcher 3
C) World of Warcraft
D) The Legend of Zelda
Richtige Antwort: D

Obviously.... Finde den Teil "wird oft" auch ganz schön weil ich es immer "The of Legend Zelda" nenne.


🧠 GPT-Rohantwort:
 Frage: Welches dieser Formen in Tetris wird auch als "T-Stück" bezeichnet?
A) Quadrat
B) L-Stück
C) Z-Stück
D) T-Stück
Richtige Antwort: D

BRUH was das für ne frage... Gibt es überhaupt T-Stücke in Tetris?
"""