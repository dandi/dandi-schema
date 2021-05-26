from hashlib import md5, sha256
import json
from pathlib import Path

from pydantic import ValidationError
import pytest

from ..consts import DANDI_SCHEMA_VERSION
from ..metadata import (
    _validate_asset_json,
    _validate_dandiset_json,
    migrate,
    publish_model_schemata,
    validate,
)

METADATA_DIR = Path(__file__).with_name("data") / "metadata"


@pytest.fixture(scope="module")
def schema_dir(tmp_path_factory):
    return publish_model_schemata(tmp_path_factory.mktemp("schema_dir"))


def test_asset(schema_dir):
    with (METADATA_DIR / "asset_001.json").open() as fp:
        data_as_dict = json.load(fp)
    # overload (here and below) schemaVersion until we support automagic schema migrations
    # under assumption that the 0.3.2 schema would be forward compatible
    data_as_dict["schemaVersion"] = DANDI_SCHEMA_VERSION
    _validate_asset_json(data_as_dict, schema_dir)


def test_dandiset(schema_dir):
    with (METADATA_DIR / "meta_000004.json").open() as fp:
        data_as_dict = json.load(fp)
    data_as_dict["schemaVersion"] = DANDI_SCHEMA_VERSION
    _validate_dandiset_json(data_as_dict, schema_dir)


def test_pydantic_validation(schema_dir):
    with (METADATA_DIR / "meta_000004.json").open() as fp:
        data_as_dict = json.load(fp)
    data_as_dict["schemaVersion"] = DANDI_SCHEMA_VERSION
    validate(data_as_dict, schema_key="Dandiset")
    validate(data_as_dict["about"][0])
    with pytest.raises(ValueError):
        validate({})


@pytest.mark.parametrize(
    "obj, schema_key, missingfields",
    [
        (
            {"schemaKey": "Dandiset"},
            None,
            {
                "assetsSummary",
                "citation",
                "contributor",
                "description",
                "id",
                "identifier",
                "license",
                "manifestLocation",
                "name",
                "version",
            },
        ),
        (
            {"schemaKey": "Dandiset"},
            "PublishedDandiset",
            {
                "assetsSummary",
                "citation",
                "contributor",
                "datePublished",
                "description",
                "doi",
                "id",
                "identifier",
                "license",
                "manifestLocation",
                "name",
                "publishedBy",
                "url",
                "version",
            },
        ),
        (
            {
                "schemaKey": "Dandiset",
                "contributor": [{"schemaKey": "Person", "roleName": ["dcite:Author"]}],
            },
            "PublishedDandiset",
            {
                "assetsSummary",
                "citation",
                "contributor",
                "datePublished",
                "description",
                "doi",
                "id",
                "identifier",
                "license",
                "manifestLocation",
                "name",
                "publishedBy",
                "url",
                "version",
            },
        ),
        (
            {
                "schemaKey": "Dandiset",
                "contributor": [
                    {
                        "schemaKey": "Person",
                        "name": "Last, first",
                        "roleName": ["dcite:ContactPerson"],
                    }
                ],
            },
            "PublishedDandiset",
            {
                "assetsSummary",
                "citation",
                "datePublished",
                "description",
                "doi",
                "id",
                "identifier",
                "license",
                "manifestLocation",
                "name",
                "publishedBy",
                "url",
                "version",
            },
        ),
        (
            {"schemaKey": "Asset"},
            None,
            {"contentSize", "encodingFormat", "id", "identifier", "path", "digest"},
        ),
        (
            {
                "schemaKey": "Asset",
                "digest": {"dandi:dandi-etag": md5(b"test").hexdigest()},
            },
            None,
            {"contentSize", "encodingFormat", "id", "identifier", "path"},
        ),
        (
            {"schemaKey": "Asset"},
            "PublishedAsset",
            {
                "datePublished",
                "contentSize",
                "publishedBy",
                "encodingFormat",
                "id",
                "identifier",
                "path",
                "digest",
            },
        ),
        (
            {
                "schemaKey": "Asset",
                "digest": {"dandi:sha2-256": sha256(b"test").hexdigest()},
            },
            "PublishedAsset",
            {
                "datePublished",
                "contentSize",
                "publishedBy",
                "encodingFormat",
                "id",
                "identifier",
                "path",
                "digest",
            },
        ),
        (
            {
                "schemaKey": "Asset",
                "digest": {"dandi:dandi-etag": md5(b"test").hexdigest()},
            },
            "PublishedAsset",
            {
                "datePublished",
                "contentSize",
                "publishedBy",
                "encodingFormat",
                "id",
                "identifier",
                "path",
                "digest",
            },
        ),
        (
            {
                "schemaKey": "Asset",
                "digest": {
                    "dandi:dandi-etag": md5(b"test").hexdigest(),
                    "dandi:sha2-256": sha256(b"test").hexdigest(),
                },
            },
            "PublishedAsset",
            {
                "datePublished",
                "contentSize",
                "publishedBy",
                "encodingFormat",
                "id",
                "identifier",
                "path",
            },
        ),
    ],
)
def test_requirements(obj, schema_key, missingfields):
    with pytest.raises(ValidationError) as exc:
        validate(obj, schema_key=schema_key)
    assert set([el["loc"][0] for el in exc.value.errors()]) == missingfields


@pytest.mark.parametrize(
    "obj, target",
    [
        ({}, "0.3.2"),
        ({"schemaVersion": "0.2.2"}, None),
        ({"schemaVersion": "0.3.0"}, "0.3.2"),
        ({"schemaVersion": "0.3.1"}, "0.3.0"),
    ],
)
def test_migrate_errors(obj, target):
    with pytest.raises(ValueError):
        migrate(obj, to_version=target)


def test_migrate_040(schema_dir):
    with (METADATA_DIR / "meta_000004old.json").open() as fp:
        data_as_dict = json.load(fp)
    with pytest.raises(ValueError) as exc:
        validate(data_as_dict)
    data_as_dict["schemaKey"] = "Dandiset"
    with pytest.raises(ValidationError) as exc:
        validate(data_as_dict)
    badfields = {
        "contributor",
        "access",
        "relatedResource",
        "id",
        "manifestLocation",
        "assetsSummary",
    }
    assert set([el["loc"][0] for el in exc.value.errors()]) == badfields
    newmeta = migrate(data_as_dict, to_version=DANDI_SCHEMA_VERSION)
    assert newmeta["schemaVersion"] == DANDI_SCHEMA_VERSION
    _validate_dandiset_json(newmeta, schema_dir)
