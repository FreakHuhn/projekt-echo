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
    result = handle_command("!status", dummy_user.copy(), "123")
    print(result)


def test_help():
    print("\n🧪 Test: !help")
    result = handle_command("!help", dummy_user.copy(), "123")
    print(result)


def test_tip():
    print("\n🧪 Test: !tip Gaming")
    result = handle_command("!tip Gaming", dummy_user.copy(), "123")
    print(result)


def test_gamequiz_struktur():
    print("\n🧪 Test: !gamequiz \"Gaming\"")
    test_user = dummy_user.copy()
    result = handle_command('!gamequiz "Gaming"', test_user, "123")
    print(result)
    print("✅ Quiz gespeichert:", "quiz" in test_user["session_state"])


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


def test_invite_parsing():
    print("\n🧪 Test: Invite-Parsing")
    command = '!invite "FreakHuhn" "EchoBot": Komm vorbei!'
    users, msg = parse_invite_command(command, sender_name="TestUser")
    print("🎯 Erkannte User:", users)
    print("📨 Nachricht:", msg)

def test_handle_invite():
    print("\n🧪 Test: !invite")
    test_user = dummy_user.copy()
    result = handle_command('!invite "FreakHuhn": Komm vorbei!', test_user, "123")
    print(result)
    print("✅ Session gesetzt:", "last_skill" in test_user["session_state"])


if __name__ == "__main__":
    print("🧪 Starte manuelle Tests für Project Echo\n")

    test_status()
    test_help()
    test_tip()
    test_gamequiz_struktur()
    test_easteregg()
    test_invite_parsing()

    print("\n✅ Alle Tests abgeschlossen.")
