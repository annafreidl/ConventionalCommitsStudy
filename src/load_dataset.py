import os
import json
import yaml
from pathlib import Path


def load_dataset(yaml_path):
    json_path = f"{os.path.dirname(yaml_path)}/{Path(yaml_path).stem}.json"

    if not os.path.exists(json_path):
        extracted_data = []

        with open(yaml_path, "r") as file:
            data = yaml.safe_load(file)
            for d in data:
                if "name" in d and "clone_url" in d:
                    extracted_data.append(
                        {
                            "name": d["name"],
                            "clone_url": d["clone_url"],
                        }
                    )

        with open(json_path, "w") as file:
            json.dump(extracted_data, file, indent=4)

        print("Loaded dataset from YAML file")

    with open(json_path, "r") as file:
        data = json.load(file)

    return data
