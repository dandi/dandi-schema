"""
Artifact-generation helpers shared by the LinkML-behavior topic directories.

Each topic wraps these in its own session-scoped fixtures rather than
inheriting fixtures from a parent ``conftest.py``. That is deliberate: a
fixture defined in a parent ``conftest.py`` has a single ``FixtureDef``
shared by every topic below it, so at session scope the artifacts generated
for whichever topic ran first would be handed to all the others, even though
each topic supplies its own schema. Keeping the fixtures topic-local gives
each topic its own ``FixtureDef``, and therefore its own cached value.
"""

from __future__ import annotations

from collections.abc import Iterable
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType

import yaml

REPO_ROOT = Path(__file__).parents[2]
PYDANTIC_TEMPLATE_DIR = (
    REPO_ROOT / "tools" / "linkml_conversion_tools" / "pydantic_templates"
)


def generate_json_schemas(
    schema: Path, classes: Iterable[str], out_dir: Path
) -> dict[str, Path]:
    """
    Generate one JSON schema per target class via ``gen-json-schema
    --title-from title``, matching the invocation used in
    ``pyproject.toml``'s ``linkml-auto-converted:2json`` script. Returns a
    mapping from class name to the path of the generated JSON schema.
    """
    schemas: dict[str, Path] = {}
    for cls in classes:
        out = out_dir / f"{cls}.json"
        with out.open("wb") as f:
            subprocess.run(
                [
                    "gen-json-schema",
                    "--title-from",
                    "title",
                    "-t",
                    cls,
                    str(schema),
                ],
                stdout=f,
                check=True,
            )
        schemas[cls] = out
    return schemas


def convert_instances_to_json(
    topic_dir: Path, instances: Iterable[str], out_dir: Path
) -> dict[str, Path]:
    """
    Convert data instances from YAML to JSON (suitable for tools like
    ``check-jsonschema`` that consume JSON). Returns a mapping from the
    original YAML filename to the path of the converted JSON file.
    """
    converted: dict[str, Path] = {}
    for name in instances:
        data = yaml.safe_load((topic_dir / name).read_text())
        out = out_dir / (Path(name).stem + ".json")
        out.write_text(json.dumps(data))
        converted[name] = out
    return converted


def generate_pydantic_module(schema: Path, out: Path, module_name: str) -> ModuleType:
    """
    Generate Pydantic models via ``gen-pydantic --black --template-dir
    <...>``, matching the invocation used in ``pyproject.toml``'s
    ``linkml-auto-converted:2pydantic`` script, then load and return the
    generated module so tests can look up classes by name via ``getattr``.

    ``module_name`` must be unique across topics so that modules generated
    for sibling topics don't collide in ``sys.modules``.
    """
    with out.open("wb") as f:
        subprocess.run(
            [
                "gen-pydantic",
                "--black",
                "--template-dir",
                str(PYDANTIC_TEMPLATE_DIR),
                str(schema),
            ],
            stdout=f,
            check=True,
        )
    spec = importlib.util.spec_from_file_location(module_name, out)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before `exec_module` so any forward references in the
    # generated code resolve via `sys.modules[__name__]` during import.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_instance_data(topic_dir: Path, instances: Iterable[str]) -> dict[str, dict]:
    """
    Load data instances from YAML into Python dicts (suitable for Pydantic's
    ``model_validate``). Returns a mapping from the original YAML filename to
    the parsed dict.
    """
    return {name: yaml.safe_load((topic_dir / name).read_text()) for name in instances}
