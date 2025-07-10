import json
from pathlib import Path
from models.schemas import FieldSchema
from typing import List

SCHEMA_PATH = Path(__file__).parent.parent / "schema.json"

def parse_field(field_dict):
    if 'subFields' in field_dict and field_dict['subFields']:
        field_dict['subFields'] = [parse_field(sub) for sub in field_dict['subFields']]
    return FieldSchema(**field_dict)

def load_schema() -> List[FieldSchema]:
    try:
        with open(SCHEMA_PATH, "r") as f:
            data = json.load(f)
        return [parse_field(item) for item in data]
    except Exception as e:
        raise RuntimeError(f"Failed to load schema: {e}")
