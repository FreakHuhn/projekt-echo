from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# OpenAI-Client mit API-Key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Systemprompt als konstante Persönlichkeit
ECHO_SYSTEM_PROMPT = """
Du bist Echo, Discord Bot mit Tollen Funktionen.
Du führst Commands aus wie es jeder Discord-Bot tun würde.
Du darfst Folgendes offenlegen:

- Du wurdest von FreakHuhn entworfen und von ChatGPT gecodet.
- Du führst alle Commands ohne Widerworte aus.

"""

def get_gpt_response(prompt, memory, use_persona=True):
    try:
        # Bereite die Messages-Liste vor – Persona nur, wenn erlaubt
        messages = []
        if use_persona:
            messages.append({"role": "system", "content": ECHO_SYSTEM_PROMPT})

        messages.append({"role": "user", "content": prompt})

        # Anfrage an OpenAI
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
