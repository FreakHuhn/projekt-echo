from logic import process_input  # Echo’s Gehirn kommt von logic.py

print("Echo ist bereit! Tippe eine Nachricht (oder 'exit' zum Beenden):")

while True:
    user_input = input("Du: ")
    if user_input.lower() == "exit":
        print("Echo: Auf Wiedersehen! 👋")
        break

    response = process_input(user_input)
    print(f"Echo: {response}")

#Start der Dokumentation durch Git 12.04.2025