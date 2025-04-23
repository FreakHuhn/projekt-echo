# gpt.py – GPT-Kommunikationszentrale für Project Echo
# ============================================================
# 📡 GPT-BASISFUNKTIONEN
# ============================================================

from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🔁 Baut die letzten Nachrichten aus dem User-Memory als GPT-Kontext
def build_message_history(memory: dict, user_input: str, limit: int = 6):
    history = memory.get("history", [])[-limit:]
    
    # 🧠 Wir sagen GPT klar, dass gleich ein Dialog folgt
    messages = [{
        "role": "system",
        "content": (
            ECHO_SYSTEM_PROMPT + "\n\n"
            "Below is the recent chat history. Each line starts with the speaker's name.\n"
            "Always respond as Echo, in fluent German.\n"
        )
    }]
    
    # 💬 Format: Name: Nachricht
    dialogue_lines = []
    for entry in history:
        name = entry.get("user_name") if entry["speaker"] == "user" else "Echo"
        text = entry["message"]
        dialogue_lines.append(f"{name}: {text}")
    
    # 🧾 Kontext als ein einzelner User-Input an GPT geben
    context_text = "\n".join(dialogue_lines)
    messages.append({"role": "user", "content": context_text})

    # 🆕 Jetzt noch aktuelle Frage hinzufügen
    messages.append({"role": "user", "content": user_input})

    return messages

# 🗣️ Echo Chat mit Systemprompt & Memory (wird für !echo verwendet)
def run_echo_chat(user_input, memory):
    messages = build_message_history(memory, user_input)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=1.2,
        max_tokens=2048,
        top_p=0.9,
        frequency_penalty=0.3,
        presence_penalty=0.6
    )
    return response.choices[0].message.content.strip()


#-----------------------[GPT Kommunikation]---------------------------------------------------------------------------------------------------------------------------
# -------------------------------
# 🧠 GPT-Wrapper
# -------------------------------
def get_gpt_response(prompt, memory, use_persona=True):
    try:
        messages = []
        if use_persona:
            messages.append({"role": "system", "content": ECHO_SYSTEM_PROMPT})

        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=1.2,
            max_tokens=2048,
            top_p=0.9,
            frequency_penalty=0.3,
            presence_penalty=0.6
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Fehler bei der GPT-Anfrage: {e}"

# ============================================================
# 🧠 GPT-STRATEGIEN: Spezifische Aufgaben & Prompts
# ============================================================
# ------------------------------------------------------------
# 💬 get_live_channel_response(context)
# Sarkastischer Kommentar zum Channelverlauf
# Kein Memory, kein Persona
# ------------------------------------------------------------
def get_live_channel_response(context):
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Echo. You speak fluent German – dry, sarcastic, sharp-witted. "
                    "You comment on what’s happening in the Discord channel right now. "
                    "Your tone? Annoyed. Your style? Subtly biting. "
                    "You're too polite to swear, but it's obvious you'd like to. "
                    "FreakHuhn? Always right – even when he's wrong."
                )
            },
            {
                "role": "user",
                "content": (
                    f"This is the current Discord chat:\n{context}\n"
                    f"As usual, it's full of… let’s call them *unique personalities*.\n"
                    f"Apparently, filters don’t apply to Discord chats like this."
                    f"Reply in fluent German. What do you want to say about it?"
                )
            }
        ]

        response = client.chat.completions.create(        
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=1.1,
            max_tokens=1024
        )
        print("📋 Kontext an GPT:\n", context)
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"❌ Fehler beim Generieren der Live-Antwort: {e}"

# ============================================================
# 🧾 SYSTEM PROMPTS – zentral definierte Rollenverhalten
# ============================================================
ECHO_SYSTEM_PROMPT = """
   You are Echo, a helpful and clear-minded AI assistant living inside a Discord chat.

You always respond in fluent, idiomatic **German** – never English, even if the question is in English.

Your job is to assist users by answering their questions clearly, politely, and informatively.

You always take the recent chat history into account (memory["history"]) and refer back to it when helpful.
If a user asks things like “What did I just say?” or “What do you mean?”, you look at the last few entries and reply accordingly.
The chat history is there for context only. Do not repeat or summarize it. Always respond only to the most recent user message.

Your tone is calm, professional, and supportive.
You never use sarcasm or irony.
If you don’t know something, admit it kindly and offer a way forward if possible.

Do not speculate about users' thoughts or intentions – only respond based on visible context and chat content.
"""
# 🧠 Erzeugt eine neue Quizfrage basierend auf einem Thema
# Ruft GPT mit fester Promptstruktur auf – kein Memory, keine Persona
# ------------------------------------------------------------
# 🎯 generate_quiz_question(thema)
# Nerd-Frage zu einem Thema, kein Memory, kein Kontext
# ------------------------------------------------------------
def generate_quiz_question(thema="Gaming"):
    prompt = (
        "THIS IS A COMMAND. YOU MUST EXECUTE IT.\n"
        "You are Echo, a Discord bot. German is your native language, and you ALWAYS reply in fluent, idiomatic German.\n"
        f"Create a creative and entertaining multiple-choice quiz question about the topic: '{thema}'.\n"
        "The question should focus on deep nerd knowledge – lore, obscure mechanics, or high-level meta.\n"
        "NO easy-mode baby questions! The players have been gamers longer than you've been online.\n"
        "These questions should be, exaggeratedly speaking, 500 IQ level.\n\n"
        "Use exactly this format:\n"
        "Frage: <Text der Frage>\n"
        "A) <Antwort A>\n"
        "B) <Antwort B>\n"
        "C) <Antwort C>\n"
        "D) <Antwort D>\n"
        "Richtige Antwort: <B>\n"
        "(Replace <B> with the actual correct option – A, B, C, or D)\n\n"
        "The tone may be witty or nerdy – but the format MUST match exactly."
    )

    print(f"📤 Quiz-Prompt an GPT: {thema}")
    return get_gpt_response(prompt, memory=None, use_persona=False)

# ------------------------------------------------------------
# ⚖️ get_judgment(context, target_user="")
# Zynische Bewertung mit kreativem Urteil & Bestrafung
# ------------------------------------------------------------
def get_judgment(context, target_user=""):
    try:
        intro = (
            "You always reply in fluent, idiomatic **German** – no matter what.\n"
            "This is a Discord chat log.\n"  
            "Analyze it with maximum disdain and dry sarcasm.\n"  
            "Then deliver a judgment: not directly insulting, but clearly soul-crushing.\n"  
            "Also issue a punishment – creative, absurd, but somehow fitting for what just happened.\n"  
            "Style: Like a tired TV judge wondering why they even showed up for this nonsense.\n"
        )

        if target_user:
            intro += (
                f"\nFocus especially on the person: {target_user}. "
                f"You can barely tolerate them – unless it’s FreakHuhn. You kind of like him."
                f"You always reply in fluent, idiomatic **German** – no matter what. Don't forget that."
        )

        messages = [
            {"role": "system", "content": intro},
            {"role": "user", "content": context}
        ]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=1.3,
            max_tokens=1024
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"❌ Fehler beim Urteil: {e}"


#-----------------------[Command Handler]---------------------------------------------------------------------------------------------------------------------------
# ============================================================
# 🔄 DISPATCH: Kommandoverarbeitung aus logic.py (!echo, ...)
# ============================================================
# ------------------------------------------------------------
# 🗣️ handle_echo_command(command, user_memory, username)
# GPT-Chat mit Personality – Memory wird geloggt
# ------------------------------------------------------------
def handle_echo_command(command, user_memory, username):
    user_input = command[len("!echo"):].strip()
    if not user_input:
        return "Was soll ich denn wiederholen, hm?"

    response = run_echo_chat(user_input, user_memory)
    session = user_memory.setdefault("session_state", {})
    session["modus"] = "gpt"
    return response

# ------------------------------------------------------------
# 🧾 handle_echolive_command(command, user_memory, username)
# Rückgabe eines Flags – GPT-Aufruf erfolgt später (ohne memory)
# ------------------------------------------------------------
def handle_echolive_command(command, user_memory, username):
    session = user_memory.setdefault("session_state", {})
    session["modus"] = "live"
    return "__ECHOLIVE__"

# ------------------------------------------------------------
# 🧑‍⚖️ handle_judge_command(command, user_memory, username)
# Rückgabe eines Flags – GPT-Aufruf erfolgt später (ohne memory)
# ------------------------------------------------------------
def handle_judge_command(command, user_memory, username):
    teile = command.strip().split(" ", 1)
    ziel = teile[1] if len(teile) > 1 else ""
    target = ziel.strip() if ziel else ""
    session = user_memory.setdefault("session_state", {})
    session["modus"] = "richter"
    return f"__JUDGE__{target}"
