# test_logic.py

import random
from logic import handle_command
from features.quiz import versuche_warhammer_easteregg
# falls wir später auch send_voice_invites testen wollen:
from features.invite import parse_invite_command, send_voice_invites

# 📦 Simulierter User-Memory für Tests
dummy_user = {
    "name": "TestUser",
    "mood": "neutral",
    "session_state": {},
    "history": []
}


def test_status():
    print("\n🧪 Test: !status")
    test_user = dummy_user.copy()
    result, _ = handle_command("!status", test_user, "123")
    print("📤 Antwort:\n", result)


def test_help():
    print("\n🧪 Test: !help")
    test_user = dummy_user.copy()
    result, _ = handle_command("!help", test_user, "123")
    print("📤 Antwort:\n", result)


def test_tip():
    print("\n🧪 Test: !tip Gaming")
    test_user = dummy_user.copy()
    result, _ = handle_command("!tip Gaming", test_user, "123")
    print("📤 Antwort:\n", result)


def test_gamequiz_struktur():
    print("\n🧪 Test: !gamequiz \"Gaming\"")
    test_user = dummy_user.copy()
    result, _ = handle_command('!gamequiz "Gaming"', test_user, "123")
    print("📤 Antwort:\n", result)
    print("✅ Quiz gesetzt?", "quiz" in test_user["session_state"])



def test_easteregg():
    print("\n🧪 Test: Warhammer-Easteregg (forced)")
    random.seed(42)  # deterministisch → kein Trigger
    result = versuche_warhammer_easteregg("Warhammer")
    print("🚫 Kein Trigger" if result is None else "💀 Easteregg aktiviert")

    random.seed(1)  # wiederholbarer Trigger
    result = versuche_warhammer_easteregg("Warhammer")
    if result:
        print("💀 Frage:", result["frage"])
        print("   Optionen:", result["optionen"])
        print("   Lösung:", result["lösung"])

def test_judge_does_not_log():
    print("\n🧪 Test: !judge Logging-Verhalten")
    test_user = dummy_user.copy()
    result, should_log = handle_command("!judge", test_user, "123")
    print("📤 Rückgabe:", result)
    print("🧠 Modus:", test_user["session_state"].get("modus"))
    print("📦 Should log:", should_log)
    print("📜 History-Einträge:", len(test_user["history"]), "→", test_user["history"])



def test_invite_parsing():
    print("\n🧪 Test: Invite-Parsing")
    command = '!invite "FreakHuhn" "EchoBot": Komm vorbei!'
    users, msg = parse_invite_command(command, sender_name="TestUser")
    print("🎯 Erkannte User:", users)
    print("📨 Nachricht:", msg)

def test_handle_invite():
    print("\n🧪 Test: !invite")
    test_user = dummy_user.copy()
    result, _ = handle_command('!invite "FreakHuhn": Komm vorbei!', test_user, "123")
    print("📤 Antwort:\n", result)
    print("✅ last_skill gesetzt?", "last_skill" in test_user["session_state"])

from logic import process_input

def test_echo_logging():
    print("\n🧪 Test: !echo Logging via process_input")
    test_user = dummy_user.copy()
    command = "!echo Sag etwas Bedeutungsvolles."

    # ✳️ Direkt in memory einsetzen
    from features.memory_io import save_memory
    memory = {"users": {"123": test_user}}
    save_memory(memory)

    # ⏎ Verarbeite den Input vollständig
    result = process_input(command, username="123", display_name="TestUser")
    print("📤 Antwort von Echo:", result)

    # 🔁 Memory neu laden, da process_input es speichert
    from features.memory_io import load_memory
    memory = load_memory()
    user_memory = memory["users"]["123"]
    history = user_memory.get("history", [])

    user_msgs = [e for e in history if e["speaker"] == "user"]
    echo_msgs = [e for e in history if e["speaker"] == "echo"]

    print("📜 Verlauf:")
    for entry in history:
        print(f" - [{entry['speaker']}] {entry['message']}")

    print("✅ User-Einträge:", len(user_msgs))
    print("✅ Echo-Einträge:", len(echo_msgs))

def test_profil_output():
    print("\n🧪 Test: !profil")

    test_user = dummy_user.copy()
    test_user["session_state"] = {
        "letzter_befehl": "!tip Gaming",
        "modus": "gpt",
        "quiz_aktiv": False
    }
    test_user["history"] = [
        {"speaker": "user", "message": "!tip Gaming"},
        {"speaker": "user", "message": "!echo wie geht's?"},
        {"speaker": "echo", "message": "Gut genug, um diesen Test zu überstehen."}
    ]

    result, _ = handle_command("!profil", test_user, "123")
    print("📤 Profil-Ausgabe:\n", result)

def test_echolive_flag():
    print("\n🧪 Test: !echolive Flag-Erkennung")

    test_user = dummy_user.copy()
    result, should_log = handle_command("!echolive", test_user, "123")

    print("📤 Rückgabe:", result)
    print("📦 should_log:", should_log)
    print("🧠 Modus:", test_user["session_state"].get("modus"))
    print("📜 History-Länge:", len(test_user["history"]))

def test_judge_flag():
    print("\n🧪 Test: !judge Flag-Erkennung")

    test_user = dummy_user.copy()
    result, should_log = handle_command("!judge @FreakHuhn", test_user, "123")

    print("📤 Rückgabe:", result)
    print("📦 should_log:", should_log)
    print("🧠 Modus:", test_user["session_state"].get("modus"))
    print("📜 History-Länge:", len(test_user["history"]))


if __name__ == "__main__":
    print("🧪 Starte manuelle Tests für Project Echo\n")

    test_status()
    test_help()
    test_tip()
    test_gamequiz_struktur()
    test_easteregg()
    test_echo_logging()
    test_invite_parsing()
    test_profil_output()
    test_echolive_flag()
    test_judge_flag()

    print("\n✅ Alle Tests abgeschlossen.")
