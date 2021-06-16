from hashlib import md5, sha256
import json
from pathlib import Path

import jsonschema
from pydantic import ValidationError
import pytest

from ..consts import DANDI_SCHEMA_VERSION
from ..metadata import (
    _validate_asset_json,
    _validate_dandiset_json,
    aggregate_assets_summary,
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
    validate(data_as_dict)


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
                "digest": {"dandi:dandi-etag": md5(b"test").hexdigest() + "-1"},
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
                "digest": {"dandi:dandi-etag": md5(b"test").hexdigest() + "-1"},
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
                    "dandi:dandi-etag": md5(b"test").hexdigest() + "-1",
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
        migrate(obj, to_version=target, skip_validation=True)


def test_migrate_041(schema_dir):
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
    with pytest.raises(jsonschema.ValidationError):
        _validate_dandiset_json(newmeta, schema_dir)
    newmeta["assetsSummary"] = {"numberOfFiles": 1, "numberOfBytes": 1}
    newmeta["manifestLocation"] = ["https://example.org/manifest"]
    _validate_dandiset_json(newmeta, schema_dir)


def test_migrate_041_access(schema_dir):
    with (METADATA_DIR / "meta_000004old.json").open() as fp:
        data_as_dict = json.load(fp)
    del data_as_dict["access"]
    newmeta = migrate(
        data_as_dict, to_version=DANDI_SCHEMA_VERSION, skip_validation=True
    )
    assert newmeta["access"] == [{"status": "dandi:OpenAccess"}]


@pytest.mark.parametrize(
    "files, summary",
    [
        (
            ("asset3_01.json", "asset3_01.json"),
            {
                "schemaKey": "AssetsSummary",
                "numberOfBytes": 18675680,
                "numberOfFiles": 2,
                "numberOfSubjects": 1,
                "numberOfSamples": 1,
                "numberOfCells": 1,
                "dataStandard": [
                    {
                        "schemaKey": "StandardsType",
                        "identifier": "RRID:SCR_015242",
                        "name": "Neurodata Without Borders (NWB)",
                    }
                ],
            },
        ),
        (
            ("asset4_01.json", "asset4_02.json"),
            {
                "schemaKey": "AssetsSummary",
                "numberOfBytes": 608720,
                "numberOfFiles": 2,
                "numberOfSubjects": 1,
                "dataStandard": [
                    {
                        "schemaKey": "StandardsType",
                        "identifier": "RRID:SCR_015242",
                        "name": "Neurodata Without Borders (NWB)",
                    }
                ],
                "approach": [
                    {
                        "schemaKey": "ApproachType",
                        "name": "electrophysiological approach",
                    },
                    {"schemaKey": "ApproachType", "name": "behavioral approach"},
                ],
                "measurementTechnique": [
                    {
                        "schemaKey": "MeasurementTechniqueType",
                        "name": "spike sorting technique",
                    },
                    {
                        "schemaKey": "MeasurementTechniqueType",
                        "name": "behavioral technique",
                    },
                    {
                        "schemaKey": "MeasurementTechniqueType",
                        "name": "surgical technique",
                    },
                ],
                "variableMeasured": ["BehavioralEvents", "Units", "ElectrodeGroup"],
                "species": [
                    {
                        "schemaKey": "SpeciesType",
                        "identifier": "http://purl.obolibrary.org/obo/NCBITaxon_10090",
                        "name": "House mouse",
                    }
                ],
            },
        ),
        (
            ("asset3_01.json", "asset4_01.json"),
            {
                "schemaKey": "AssetsSummary",
                "numberOfBytes": 9687568,
                "numberOfFiles": 2,
                "numberOfSubjects": 2,
                "numberOfSamples": 1,
                "numberOfCells": 1,
                "dataStandard": [
                    {
                        "schemaKey": "StandardsType",
                        "identifier": "RRID:SCR_015242",
                        "name": "Neurodata Without Borders (NWB)",
                    }
                ],
                "approach": [
                    {
                        "schemaKey": "ApproachType",
                        "name": "electrophysiological approach",
                    },
                    {"schemaKey": "ApproachType", "name": "behavioral approach"},
                ],
                "measurementTechnique": [
                    {
                        "schemaKey": "MeasurementTechniqueType",
                        "name": "spike sorting technique",
                    },
                    {
                        "schemaKey": "MeasurementTechniqueType",
                        "name": "behavioral technique",
                    },
                    {
                        "schemaKey": "MeasurementTechniqueType",
                        "name": "surgical technique",
                    },
                ],
                "variableMeasured": ["BehavioralEvents", "Units", "ElectrodeGroup"],
                "species": [
                    {
                        "schemaKey": "SpeciesType",
                        "identifier": "http://purl.obolibrary.org/obo/NCBITaxon_10090",
                        "name": "House mouse",
                    }
                ],
            },
        ),
    ],
)
def test_aggregate(files, summary):
    metadata = (json.loads((METADATA_DIR / f).read_text()) for f in files)
    metadata_summary = aggregate_assets_summary(metadata)
    assert metadata_summary.json_dict() == summary
