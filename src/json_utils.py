import json


def load_json(file_path):
    """
    Lädt JSON-Daten aus einer Datei.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Datei {file_path} nicht gefunden.")
        return None
    except json.JSONDecodeError as e:
        print(f"Fehler beim Laden der JSON-Datei {file_path}: {e}")
        return None
