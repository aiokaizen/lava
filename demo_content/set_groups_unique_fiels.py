"""
    This script was used to rectify 'groups.json' file.
"""
import json
import pathlib


path = pathlib.Path().resolve()
parent_dir = path / "lava" / "demo_content"
filename = parent_dir / "groups.json"

new_data = []

with open(filename, "r") as f:
    data = json.load(f)
    existing_groupe_names = []
    new_data = []
    index = 1
    for row in data:
        if not row["name"] in existing_groupe_names:
            row["id"] = index
            new_data.append(row)
            existing_groupe_names.append(row["name"])
            index += 1

with open(parent_dir / "groups2.json", "w") as f:
    json.dump(new_data, f, indent=4)
