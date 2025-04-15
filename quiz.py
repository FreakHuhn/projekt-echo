from gpt import get_gpt_response
import re

# 🧠 Generiert eine Multiple-Choice-Quizfrage mithilfe von GPT
# Gibt ein Dictionary zurück mit Frage, vier Antwortoptionen und der richtigen Antwort

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

    antwort = get_gpt_response(prompt, memory, use_persona=False)

    print("🧠 GPT raw response:\n", antwort)

    return parse_quizantwort(antwort)

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

# ✅ Prüft, ob die gegebene Antwort korrekt ist
# Gibt True oder False zurück – vergleicht User-Antwort mit der GPT-Lösung

def pruefe_antwort(user_input, session):
    loesung = session.get("quiz", {}).get("lösung", "?")
    antwort = user_input.strip().upper()
    print(f"📊 Antwortprüfung – Spieler: {antwort}, Lösung: {loesung}")
    return antwort == loesung
