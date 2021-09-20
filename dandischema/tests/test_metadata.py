from hashlib import md5, sha256
import json
from pathlib import Path

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
    data_as_dict["schemaVersion"] = "0.4.4"
    validate(data_as_dict, schema_key="Dandiset", json_validation=True)
    data_as_dict["schemaVersion"] = DANDI_SCHEMA_VERSION
    validate(data_as_dict, schema_key="Dandiset", json_validation=True)
    validate(data_as_dict["about"][0])
    with pytest.raises(ValueError):
        validate({})


def test_json_schemakey_validation():
    with pytest.raises(ValueError) as exc:
        validate(
            {"identifier": "DANDI:000000", "schemaVersion": "0.4.4"},
            json_validation=True,
            schema_key="Dandiset",
            schema_version="0.6.0",
        )
    assert "'schemaKey' is a required property" in str(exc.value)


@pytest.mark.parametrize(
    "schema_version, schema_key",
    [
        ("0.4.2", "Dandiset"),
        ("0.4.2", "PublishedDandiset"),
        ("0.4.2", "Asset"),
        ("0.4.2", "PublishedAsset"),
    ],
)
def test_mismatch_key(schema_version, schema_key):
    with pytest.raises(ValueError):
        validate({}, schema_version=schema_version, schema_key=schema_key)


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
            {
                "contentSize",
                "encodingFormat",
                "id",
                "identifier",
                "path",
                "digest",
                "contentUrl",
            },
        ),
        (
            {
                "schemaKey": "Asset",
                "digest": {"dandi:dandi-etag": md5(b"test").hexdigest() + "-1"},
            },
            None,
            {"contentSize", "encodingFormat", "id", "identifier", "path", "contentUrl"},
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
                "contentUrl",
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
                "contentUrl",
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
                "contentUrl",
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
                "contentUrl",
            },
        ),
    ],
)
def test_requirements(obj, schema_key, missingfields):
    with pytest.raises(ValueError):
        validate(obj, schema_key=schema_key)
    with pytest.raises(ValidationError) as exc:
        validate(obj, schema_key=schema_key, schema_version=DANDI_SCHEMA_VERSION)
    assert set([el["loc"][0] for el in exc.value.errors()]) == missingfields


@pytest.mark.parametrize(
    "obj, schema_key, errors, num_errors",
    [
        (
            {"schemaKey": "Dandiset", "schemaVersion": "0.4.4"},
            None,
            {"field required"},
            10,
        ),
        (
            {
                "schemaKey": "Dandiset",
                "identifier": "DANDI:000000",
                "schemaVersion": "0.4.4",
            },
            None,
            {"field required"},
            9,
        ),
    ],
)
def test_missing_ok(obj, schema_key, errors, num_errors):
    validate(
        obj, schema_key=schema_key, schema_version=DANDI_SCHEMA_VERSION, missing_ok=True
    )
    with pytest.raises(ValueError) as exc:
        validate(obj, schema_key=schema_key, schema_version=DANDI_SCHEMA_VERSION)
    exc_errors = [el["msg"] for el in exc.value.errors()]
    assert len(exc_errors) == num_errors
    assert set(exc_errors) == errors


def test_missing_ok_error():
    with pytest.raises(ValueError):
        validate(
            {
                "schemaKey": "Dandiset",
                "identifier": "000000",
                "schemaVersion": "0.4.4",
            },
            json_validation=True,
            missing_ok=True,
        )
    with pytest.raises(ValueError):
        validate(
            {
                "schemaKey": "Dandiset",
                "identifier": "000000",
                "schemaVersion": "0.4.4",
            },
            missing_ok=True,
        )


@pytest.mark.parametrize(
    "obj, target",
    [
        ({}, "0.6.0"),
        ({"schemaVersion": "0.4.4"}, None),
        ({"schemaVersion": "0.4.4"}, "0.4.6"),
        ({"schemaVersion": "0.6.0"}, "0.5.2"),
    ],
)
def test_migrate_errors(obj, target):
    with pytest.raises(ValueError):
        migrate(obj, to_version=target, skip_validation=True)


def test_migrate_044(schema_dir):
    with (METADATA_DIR / "meta_000004old.json").open() as fp:
        data_as_dict = json.load(fp)
    with pytest.raises(ValueError):
        validate(data_as_dict)
    data_as_dict["schemaKey"] = "Dandiset"
    with pytest.raises(ValueError):
        migrate(data_as_dict, to_version=DANDI_SCHEMA_VERSION)
    data_as_dict["about"].pop()
    newmeta = migrate(data_as_dict, to_version=DANDI_SCHEMA_VERSION)
    assert newmeta["schemaVersion"] == DANDI_SCHEMA_VERSION
    assert newmeta["access"] == [
        {
            "status": "dandi:OpenAccess",
            "contactPoint": {"schemaKey": "ContactPoint"},
            "schemaKey": "AccessRequirements",
        }
    ]

    # if already the target version - we do not change it, and do not crash
    newmeta_2 = migrate(newmeta, to_version=DANDI_SCHEMA_VERSION)
    assert newmeta_2 == newmeta
    assert newmeta_2 is not newmeta  # but we do create a copy


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
                "approach": [],
                "measurementTechnique": [],
                "variableMeasured": [],
                "species": [],
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
    assert aggregate_assets_summary(metadata) == summary


def test_aggregate_norecord():
    assert aggregate_assets_summary([]) == {
        "numberOfBytes": 0,
        "numberOfFiles": 0,
        "schemaKey": "AssetsSummary",
    }


@pytest.mark.parametrize(
    "version", ["0.1.0", DANDI_SCHEMA_VERSION.rsplit(".", 1)[0], "10000.0.0"]
)
def test_aggregate_nonsupported(version):
    with pytest.raises(ValueError) as exc:
        aggregate_assets_summary([{"schemaVersion": version}])
    assert "Allowed are" in str(exc)
    assert DANDI_SCHEMA_VERSION in str(exc)
    assert version in str(exc)
