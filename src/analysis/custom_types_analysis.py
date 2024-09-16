import json
import os
from pathlib import Path

CUSTOM_TYPES_FILE_PATH = Path(__file__).resolve().parents[1] / "results" / "custom_types.json"


def save_custom_types(custom_types, file_path=CUSTOM_TYPES_FILE_PATH):
    """
    Speichert die custom commit types in eine JSON-Datei. Doppelte Einträge sind erlaubt.
    """
    # Prüfen, ob die Datei existiert
    if not os.path.exists(file_path):
        with open(file_path, 'w') as json_file:
            json.dump([], json_file, indent=4)

    # Existierende Typen laden
    try:
        with open(file_path, 'r') as json_file:
            existing_custom_types = json.load(json_file)
    except (json.JSONDecodeError, FileNotFoundError):
        existing_custom_types = []

    # Neue Typen hinzufügen, Duplikate sind erlaubt
    updated_custom_types = existing_custom_types + custom_types

    # Speichern der aktualisierten Typen
    with open(file_path, 'w') as json_file:
        json.dump(updated_custom_types, json_file, indent=4)

    # Custom Types zurücksetzen
    custom_types.clear()
