from __future__ import annotations

from pathlib import Path
from types import ModuleType

import pytest

from .._generation import (
    convert_instances_to_json,
    generate_json_schemas,
    generate_pydantic_module,
    load_instance_data,
)

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
    return generate_json_schemas(
        SCHEMA, CLASSES, tmp_path_factory.mktemp("json_schemas")
    )


@pytest.fixture(scope="session")
def json_instances(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    return convert_instances_to_json(
        HERE, INSTANCES, tmp_path_factory.mktemp("json_instances")
    )


@pytest.fixture(scope="session")
def pydantic_module(tmp_path_factory: pytest.TempPathFactory) -> ModuleType:
    return generate_pydantic_module(
        SCHEMA,
        tmp_path_factory.mktemp("pydantic") / "models_linkml.py",
        f"models_linkml_{HERE.name}",
    )


@pytest.fixture(scope="session")
def instance_data() -> dict[str, dict]:
    return load_instance_data(HERE, INSTANCES)
