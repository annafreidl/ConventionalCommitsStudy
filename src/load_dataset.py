import json
import yaml
from pathlib import Path


def load_dataset(yaml_path):
    json_path = Path(yaml_path).with_suffix('.json')

    if not json_path.exists():

        with open(yaml_path, "r", encoding='utf-8') as file:
            data = yaml.safe_load(file)

        extracted_data = [
            {"name": d["name"], "clone_url": d["clone_url"]}
            for d in data if "name" in d and "clone_url" in d
        ]

        with open(json_path, "w", encoding='utf-8') as file:
            json.dump(extracted_data, file, indent=4)

        print("Loaded dataset from YAML file")
    else:
        with open(json_path, "r") as file:
            extracted_data = json.load(file)

    return extracted_data
