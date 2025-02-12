from hashlib import md5, sha256
import json
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Set

import pytest

from .utils import skipif_no_network
from ..consts import DANDI_SCHEMA_VERSION
from ..exceptions import JsonschemaValidationError, PydanticValidationError
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
def schema_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return publish_model_schemata(tmp_path_factory.mktemp("schema_dir"))


def test_asset(schema_dir: Path) -> None:
    with (METADATA_DIR / "asset_001.json").open() as fp:
        data_as_dict = json.load(fp)
    # overload (here and below) schemaVersion until we support automagic schema migrations
    # under assumption that the 0.3.2 schema would be forward compatible
    data_as_dict["schemaVersion"] = DANDI_SCHEMA_VERSION
    _validate_asset_json(data_as_dict, schema_dir)
    validate(data_as_dict)


def test_dandiset(schema_dir: Path) -> None:
    with (METADATA_DIR / "meta_000004.json").open() as fp:
        data_as_dict = json.load(fp)
    data_as_dict["schemaVersion"] = DANDI_SCHEMA_VERSION
    _validate_dandiset_json(data_as_dict, schema_dir)


def test_id(schema_dir: Path) -> None:
    with open(schema_dir / "context.json") as fp:
        context = json.load(fp)
    assert context["@context"]["hasMember"]["@type"] == "@id"


@skipif_no_network
def test_pydantic_validation(schema_dir: Path) -> None:
    with (METADATA_DIR / "meta_000004.json").open() as fp:
        data_as_dict = json.load(fp)
    data_as_dict["schemaVersion"] = "0.4.4"
    validate(data_as_dict, schema_key="Dandiset", json_validation=True)
    data_as_dict["schemaVersion"] = DANDI_SCHEMA_VERSION
    validate(data_as_dict, schema_key="Dandiset", json_validation=True)
    validate(data_as_dict["about"][0])
    with pytest.raises(ValueError):
        validate({})


@skipif_no_network
def test_json_schemakey_validation() -> None:
    with pytest.raises(JsonschemaValidationError) as exc:
        validate(
            {"identifier": "DANDI:000000", "schemaVersion": "0.4.4"},
            json_validation=True,
            schema_key="Dandiset",
            schema_version="0.6.0",
        )
    assert "'schemaKey' is a required property" in str(exc.value.errors)


@pytest.mark.parametrize(
    "schema_version, schema_key",
    [
        ("0.4.2", "Dandiset"),
        ("0.4.2", "PublishedDandiset"),
        ("0.4.2", "Asset"),
        ("0.4.2", "PublishedAsset"),
    ],
)
def test_mismatch_key(schema_version: str, schema_key: str) -> None:
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
                        "email": "nobody@example.com",
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
def test_requirements(
    obj: Dict[str, Any], schema_key: Optional[str], missingfields: Set[str]
) -> None:
    with pytest.raises(ValueError):
        validate(obj, schema_key=schema_key)
    with pytest.raises(PydanticValidationError) as exc:
        validate(obj, schema_key=schema_key, schema_version=DANDI_SCHEMA_VERSION)
    assert set([el["loc"][0] for el in exc.value.errors]) == missingfields


@pytest.mark.parametrize(
    "obj, schema_key, errors, num_errors",
    [
        (
            {"schemaKey": "Dandiset", "schemaVersion": "0.4.4"},
            None,
            {"Field required"},
            10,
        ),
        (
            {
                "schemaKey": "Dandiset",
                "identifier": "DANDI:000000",
                "schemaVersion": "0.4.4",
            },
            None,
            {"Field required"},
            9,
        ),
    ],
)
def test_missing_ok(
    obj: Dict[str, Any], schema_key: Optional[str], errors: Set[str], num_errors: int
) -> None:
    validate(
        obj, schema_key=schema_key, schema_version=DANDI_SCHEMA_VERSION, missing_ok=True
    )
    with pytest.raises(PydanticValidationError) as exc:
        validate(obj, schema_key=schema_key, schema_version=DANDI_SCHEMA_VERSION)
    exc_errors = [el["msg"] for el in exc.value.errors]
    assert len(exc_errors) == num_errors
    assert set(exc_errors) == errors


@skipif_no_network
def test_missing_ok_error() -> None:
    with pytest.raises(JsonschemaValidationError):
        validate(
            {
                "schemaKey": "Dandiset",
                "identifier": "000000",
                "schemaVersion": "0.4.4",
            },
            json_validation=True,
            missing_ok=True,
        )
    with pytest.raises(PydanticValidationError):
        validate(
            {
                "schemaKey": "Dandiset",
                "identifier": "000000",
                "schemaVersion": "0.4.4",
            },
            missing_ok=True,
        )


@pytest.mark.parametrize(
    "obj, target, msg",
    [
        ({}, "0.6.0", "does not have a `schemaVersion` field"),
        # Non-string `schemaVersion` field in the instance
        ({"schemaVersion": 42}, DANDI_SCHEMA_VERSION, "has a non-string"),
        # `schemaVersion` field in the instance with invalid format
        (
            {"schemaVersion": "abc"},
            DANDI_SCHEMA_VERSION,
            "has an invalid `schemaVersion` field",
        ),
        # `schemaVersion` field in the instance is not an allowed input schema
        (
            {"schemaVersion": "0.4.5"},
            DANDI_SCHEMA_VERSION,
            "is not one of the supported versions "
            "for input Dandiset metadata instances",
        ),
        # target schema with invalid format
        (
            {"schemaVersion": "0.4.4"},
            "cba",
            "target version.* is not a valid DANDI schema version",
        ),
        # target schema is not an allowed target schema
        (
            {"schemaVersion": "0.4.4"},
            "0.4.5",
            "Target version, .*, is not among supported target schemas",
        ),
    ],
)
def test_migrate_value_errors(obj: Dict[str, Any], target: Any, msg: str) -> None:
    """
    Test cases when `migrate()` is expected to raise a `ValueError` exception

    :param obj: The metadata instance of `Dandiset` to migrate
    :param target: The target DANDI schema version to migrate to
    :param msg: The expected error message with in the raised exception
    """
    with pytest.raises(ValueError, match=msg):
        migrate(obj, to_version=target, skip_validation=True)


def test_migrate_value_errors_lesser_target(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test cases when `migrate()` is expected to raise a `ValueError` exception
    when the target schema version is lesser than the schema version of the metadata
    instance
    """
    from dandischema import metadata

    monkeypatch.setattr(metadata, "ALLOWED_TARGET_SCHEMAS", ["0.6.0"])

    with pytest.raises(ValueError, match="Cannot migrate from .* to lower"):
        migrate({"schemaVersion": "0.6.7"}, to_version="0.6.0", skip_validation=True)


@skipif_no_network
def test_migrate_044(schema_dir: Path) -> None:
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
def test_aggregate(files: Sequence[str], summary: Dict[str, Any]) -> None:
    metadata = (json.loads((METADATA_DIR / f).read_text()) for f in files)
    assert aggregate_assets_summary(metadata) == summary


def test_aggregate_norecord() -> None:
    assert aggregate_assets_summary([]) == {
        "numberOfBytes": 0,
        "numberOfFiles": 0,
        "schemaKey": "AssetsSummary",
    }


@pytest.mark.parametrize(
    "version", ["0.1.0", DANDI_SCHEMA_VERSION.rsplit(".", 1)[0], "10000.0.0"]
)
def test_aggregate_nonsupported(version: str) -> None:
    with pytest.raises(ValueError) as exc:
        aggregate_assets_summary([{"schemaVersion": version}])
    assert "Allowed are" in str(exc)
    assert DANDI_SCHEMA_VERSION in str(exc)
    assert version in str(exc)


@skipif_no_network
def test_validate_older() -> None:
    with pytest.raises(ValueError):
        validate(
            {"schemaVersion": "0.5.2", "schemaKey": "Anykey"}, json_validation=True
        )
    with pytest.raises(JsonschemaValidationError):
        validate({"schemaVersion": "0.5.2", "schemaKey": "Asset"}, json_validation=True)
    with pytest.raises(JsonschemaValidationError):
        validate(
            {"schemaVersion": DANDI_SCHEMA_VERSION, "schemaKey": "Asset"},
            json_validation=True,
        )


def test_aggregation_bids() -> None:
    data = [
        {
            "id": "dandiasset:6668d37f-e842-4b73-8c20-082a1dd0d31a",
            "path": "sub-MITU01/ses-20210703h01m05s04/microscopy/sub-MITU01_"
            "run-1_sample-163_stain-YO_chunk-5_spim.ome.zarr",
            "access": [
                {"status": "dandi:OpenAccess", "schemaKey": "AccessRequirements"}
            ],
            "digest": {
                "dandi:dandi-etag": "7e002a08bef16abb5954d1c2a3fce0a2-574",
            },
            "@context": "https://raw.githubusercontent.com/dandi/schema/master/"
            "releases/0.4.4/context.json",
            "schemaKey": "Asset",
            "contentUrl": [
                "https://api.dandiarchive.org/api/assets/6668d37f-e842-4b73-8c20"
                "-082a1dd0d31a/download/",
            ],
            "identifier": "6668d37f-e842-4b73-8c20-082a1dd0d31a",
            "repository": "https://dandiarchive.org/",
            "contentSize": 38474544973,
            "dateModified": "2021-07-22T23:59:16.060551-04:00",
            "schemaVersion": "0.4.4",
            "encodingFormat": "application/x-zarr",
            "blobDateModified": "2021-07-11T16:34:31-04:00",
        },
        {
            "id": "dandiasset:84dd580f-8d4a-43f8-bda3-6fb53fb5d3a2",
            "path": "sub-MITU01/ses-20210703h16m32s10/microscopy/sub-MITU01_"
            "ses-20210703h16m32s10_run-1_sample-162_stain-LEC_chunk-5_spim.ome.zarr",
            "access": [
                {"status": "dandi:OpenAccess", "schemaKey": "AccessRequirements"}
            ],
            "digest": {
                "dandi:dandi-etag": "954aab90c420c621cc70d17e74a65116-921",
            },
            "@context": "https://raw.githubusercontent.com/dandi/schema/master/"
            "releases/0.6.0/context.json",
            "schemaKey": "Asset",
            "contentUrl": [
                "https://api.dandiarchive.org/api/assets/84dd580f-8d4a-43f8-bda3"
                "-6fb53fb5d3a2/download/",
            ],
            "identifier": "84dd580f-8d4a-43f8-bda3-6fb53fb5d3a2",
            "repository": "https://dandiarchive.org/",
            "contentSize": 61774316916,
            "dateModified": "2021-10-01T18:28:16.038990-04:00",
            "schemaVersion": "0.6.0",
            "encodingFormat": "application/x-zarr",
            "blobDateModified": "2021-07-10T18:58:25-04:00",
        },
        {
            "@context": "https://raw.githubusercontent.com/dandi/shortened",
            "schemaKey": "Asset",
            "repository": "https://dandiarchive.org/",
            "dateModified": "2021-10-05T13:08:07.855880-04:00",
            "schemaVersion": "0.6.0",
            "encodingFormat": "application/json",
            "blobDateModified": "2021-10-04T15:58:52.266222-04:00",
            "id": "dandiasset:34e30fa6-cf6a-4a32-90cb-b06f6f2f30a6",
            "access": [
                {"schemaKey": "AccessRequirements", "status": "dandi:OpenAccess"}
            ],
            "path": "dataset_description.json",
            "identifier": "34e30fa6-cf6a-4a32-90cb-b06f6f2f30a6",
            "contentUrl": [
                "https://api.dandiarchive.org/api/assets/shortened",
            ],
            "contentSize": 3377,
            "digest": {
                "dandi:dandi-etag": "88c82d75b1119393b9ee49adc14714f3-1",
            },
        },
    ]
    summary = aggregate_assets_summary(data)
    assert summary["numberOfFiles"] == 3
    assert summary["numberOfSamples"] == 2
    assert summary["numberOfSubjects"] == 1
    assert sum("BIDS" in _.get("name", "") for _ in summary["dataStandard"]) == 1
    assert (
        sum(_.get("name", "").startswith("OME/NGFF") for _ in summary["dataStandard"])
        == 1
    )  # only a single entry so we do not duplicate them
