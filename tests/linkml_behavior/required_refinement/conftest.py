from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType

import pytest
import yaml

HERE = Path(__file__).parent
SCHEMA = HERE / "schema.yaml"
REPO_ROOT = HERE.parents[2]
PYDANTIC_TEMPLATE_DIR = (
    REPO_ROOT / "tools" / "linkml_conversion_tools" / "pydantic_templates"
)

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


@pytest.fixture(scope="session")
def pydantic_module(tmp_path_factory: pytest.TempPathFactory) -> ModuleType:
    """
    Pydantic models generated once from ``schema.yaml`` via
    ``gen-pydantic --black --template-dir <...>``, matching the invocation
    used in ``pyproject.toml``'s ``linkml-auto-converted:2pydantic``
    script. The generated module is loaded and returned so tests can look
    up classes by name via ``getattr``.
    """
    out_dir = tmp_path_factory.mktemp("pydantic")
    out = out_dir / "models_linkml.py"
    with out.open("wb") as f:
        subprocess.run(
            [
                "gen-pydantic",
                "--black",
                "--template-dir",
                str(PYDANTIC_TEMPLATE_DIR),
                str(SCHEMA),
            ],
            stdout=f,
            check=True,
        )
    # Suffix the module name with the topic folder so sibling
    # `tests/linkml_behavior/<other_topic>/` fixtures don't collide in
    # `sys.modules`.
    spec = importlib.util.spec_from_file_location(f"models_linkml_{HERE.name}", out)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before `exec_module` so any forward references in the
    # generated code resolve via `sys.modules[__name__]` during import.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def instance_data() -> dict[str, dict]:
    """
    Data instances in YAML loaded once into Python dicts (suitable for
    Pydantic's ``model_validate``). Returns a mapping from the original
    YAML filename to the parsed dict.
    """
    return {name: yaml.safe_load((HERE / name).read_text()) for name in INSTANCES}
