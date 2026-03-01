import json
from jsonschema import validate
from pathlib import Path

def test_example_validates():
    schema = json.loads(Path("schemas/requirement.v1.json").read_text(encoding="utf-8"))
    example = json.loads(Path("examples/requirement_example.json").read_text(encoding="utf-8"))
    validate(instance=example, schema=schema)
