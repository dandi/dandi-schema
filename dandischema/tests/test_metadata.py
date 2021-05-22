import json
from pathlib import Path

import pytest

from ..consts import DANDI_SCHEMA_VERSION
from ..metadata import (
    publish_model_schemata,
    validate,
    validate_asset_json,
    validate_dandiset_json,
)

METADATA_DIR = Path(__file__).with_name("data") / "metadata"


@pytest.fixture(scope="module")
def schema_dir(tmp_path_factory):
    return publish_model_schemata(tmp_path_factory.mktemp("schema_dir"))


def test_asset(schema_dir):
    with (METADATA_DIR / "asset_001.json").open() as fp:
        data_as_dict = json.load(fp)
    data_as_dict["schemaVersion"] = DANDI_SCHEMA_VERSION
    validate_asset_json(data_as_dict, schema_dir)


def test_dandiset(schema_dir):
    with (METADATA_DIR / "meta_000004.json").open() as fp:
        data_as_dict = json.load(fp)
    data_as_dict["schemaVersion"] = DANDI_SCHEMA_VERSION
    validate_dandiset_json(data_as_dict, schema_dir)


def test_dandiset_pydantic(schema_dir):
    with (METADATA_DIR / "meta_000004.json").open() as fp:
        data_as_dict = json.load(fp)
    data_as_dict["schemaVersion"] = DANDI_SCHEMA_VERSION
    validate(data_as_dict, schema_key="DandisetMeta")
    validate(data_as_dict["about"][0])
    with pytest.raises(ValueError):
        validate({})
