# features/memory_io.py
import json

MEMORY_FILE = "memory.json"

# 🔁 Lädt das Memory-File
def load_memory():
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

# 💾 Speichert das Memory-File
def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)
