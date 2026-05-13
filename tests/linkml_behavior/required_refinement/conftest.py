from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest
import yaml

HERE = Path(__file__).parent
SCHEMA = HERE / "schema.yaml"

CLASSES = ("Person", "Employee")
INSTANCES = (
    "valid_instance.yaml",
    "missing_name_instance.yaml",
    "bad_type_instance.yaml",
)


@pytest.fixture(scope="session")
def json_schemas(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """
    Per-target-class JSON schemas generated once from ``schema.yaml`` via
    ``gen-json-schema --title-from title``, matching the invocation used in
    ``pyproject.toml``'s ``linkml-auto-converted:2json`` script. Returns a
    mapping from class name to the path of the generated JSON schema.
    """
    out_dir = tmp_path_factory.mktemp("json_schemas")
    schemas: dict[str, Path] = {}
    for cls in CLASSES:
        out = out_dir / f"{cls}.json"
        with out.open("wb") as f:
            subprocess.run(
                [
                    "gen-json-schema",
                    "--title-from",
                    "title",
                    "-t",
                    cls,
                    str(SCHEMA),
                ],
                stdout=f,
                check=True,
            )
        schemas[cls] = out
    return schemas


@pytest.fixture(scope="session")
def json_instances(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """
    Data instances in YAML converted once to JSON (suitable for tools like
    ``check-jsonschema`` that consume JSON). Returns a mapping from the
    original YAML filename to the path of the converted JSON file.
    """
    out_dir = tmp_path_factory.mktemp("json_instances")
    instances: dict[str, Path] = {}
    for name in INSTANCES:
        data = yaml.safe_load((HERE / name).read_text())
        out = out_dir / (Path(name).stem + ".json")
        out.write_text(json.dumps(data))
        instances[name] = out
    return instances
