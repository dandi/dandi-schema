from contextlib import nullcontext
from hashlib import md5, sha256
import json
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Set
from unittest.mock import MagicMock, patch

from jsonschema.protocols import Validator as JsonschemaValidator
from pydantic import BaseModel
import pytest

from dandischema.models import Asset, Dandiset, PublishedAsset, PublishedDandiset
from dandischema.utils import TransitionalGenerateJsonSchema, jsonschema_validator

from .utils import (
    DANDISET_METADATA_DIR,
    DOI_PREFIX,
    INSTANCE_NAME,
    METADATA_DIR,
    skipif_instance_name_not_dandi,
    skipif_no_network,
    skipif_no_test_dandiset_metadata_dir,
)
from ..consts import DANDI_SCHEMA_VERSION
from ..exceptions import JsonschemaValidationError, PydanticValidationError
from ..metadata import (
    _get_jsonschema_validator,
    _get_jsonschema_validator_local,
    _validate_asset_json,
    _validate_dandiset_json,
    _validate_obj_json,
    aggregate_assets_summary,
    migrate,
    publish_model_schemata,
    validate,
)


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


@skipif_no_test_dandiset_metadata_dir
def test_dandiset(schema_dir: Path) -> None:
    with (DANDISET_METADATA_DIR / "meta_000004.json").open() as fp:
        data_as_dict = json.load(fp)
    data_as_dict["schemaVersion"] = DANDI_SCHEMA_VERSION
    _validate_dandiset_json(data_as_dict, schema_dir)


def test_id(schema_dir: Path) -> None:
    with open(schema_dir / "context.json") as fp:
        context = json.load(fp)
    assert context["@context"]["hasMember"]["@type"] == "@id"


@skipif_no_network
@skipif_no_test_dandiset_metadata_dir
def test_pydantic_validation(schema_dir: Path) -> None:
    with (DANDISET_METADATA_DIR / "meta_000004.json").open() as fp:
        data_as_dict = json.load(fp)
    data_as_dict["schemaVersion"] = "0.4.4"
    if INSTANCE_NAME == "DANDI":
        # This is run only when the DANDI instance is `"DANDI"`
        # since the JSON schema at `0.4.4` is hardcoded to only
        # for an instance named `DANDI`
        validate(data_as_dict, schema_key="Dandiset", json_validation=True)
    data_as_dict["schemaVersion"] = DANDI_SCHEMA_VERSION
    validate(data_as_dict, schema_key="Dandiset", json_validation=True)
    validate(data_as_dict["about"][0])
    with pytest.raises(ValueError):
        validate({})


@skipif_no_network
# Skip for when the instance being tested is not `DANDI` since the JSON schema
# version at `0.4.4` and `0.6.0` is hardcoded to only for an instance named `DANDI`
@skipif_instance_name_not_dandi
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
                e
                for e in [
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
                ]
                if DOI_PREFIX is not None or e != "doi"
            },
        ),
        (
            {
                "schemaKey": "Dandiset",
                "contributor": [{"schemaKey": "Person", "roleName": ["dcite:Author"]}],
            },
            "PublishedDandiset",
            {
                e
                for e in [
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
                ]
                if DOI_PREFIX is not None or e != "doi"
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
                e
                for e in [
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
                ]
                if DOI_PREFIX is not None or e != "doi"
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
                "identifier": f"{INSTANCE_NAME}:000000",
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
    if INSTANCE_NAME == "DANDI":
        # Skip for when the instance being tested is not `DANDI` since the JSON schema
        # version at `0.4.4` is hardcoded to only for an instance named `DANDI`
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
@skipif_no_test_dandiset_metadata_dir
# Skip for instance name not being DANDI because JSON schema version at `0.4.4`, the
# schema version of the metadata in `meta_000004old.json`, is hardcoded to only for
# an DANDI instance named `DANDI`
@skipif_instance_name_not_dandi
def test_migrate_044(schema_dir: Path) -> None:
    with (DANDISET_METADATA_DIR / "meta_000004old.json").open() as fp:
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
    newmeta_2 = migrate(
        newmeta,
        to_version=DANDI_SCHEMA_VERSION,
        # to avoid possible crash due to attempt to download not yet
        # released schema if we are still working within yet to be
        # released version of the schema
        skip_validation=True,
    )
    assert newmeta_2 == newmeta
    assert newmeta_2 is not newmeta  # but we do create a copy


def test_migrate_schemaversion_update() -> None:
    """
    Test that migrate() always updates schemaVersion to target version,
    even when migrating from 0.6.0+ to higher versions.

    This is a regression test for the bug where schemaVersion was only
    updated for migrations from versions < 0.6.0.
    """
    # Test migrating from 0.6.0 to current version
    obj_060 = {
        "schemaKey": "Dandiset",
        "schemaVersion": "0.6.0",
        "identifier": "DANDI:000000",
    }
    result = migrate(obj_060, to_version=DANDI_SCHEMA_VERSION, skip_validation=True)
    assert result["schemaVersion"] == DANDI_SCHEMA_VERSION, (
        f"Expected schemaVersion to be {DANDI_SCHEMA_VERSION}, "
        f"but got {result['schemaVersion']}"
    )

    # Test migrating from 0.6.4 to current version
    obj_064 = {
        "schemaKey": "Dandiset",
        "schemaVersion": "0.6.4",
        "identifier": "DANDI:000000",
    }
    result = migrate(obj_064, to_version=DANDI_SCHEMA_VERSION, skip_validation=True)
    assert result["schemaVersion"] == DANDI_SCHEMA_VERSION, (
        f"Expected schemaVersion to be {DANDI_SCHEMA_VERSION}, "
        f"but got {result['schemaVersion']}"
    )


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
    if INSTANCE_NAME == "DANDI":
        # Skip for when the instance being tested is not `DANDI` since the JSON schema
        # version at `0.5.2` is hardcoded to only for an instance named `DANDI`
        with pytest.raises(ValueError):
            validate(
                {"schemaVersion": "0.5.2", "schemaKey": "Anykey"}, json_validation=True
            )
        with pytest.raises(JsonschemaValidationError):
            validate(
                {"schemaVersion": "0.5.2", "schemaKey": "Asset"}, json_validation=True
            )
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


def test_hed_standard_structure() -> None:
    from dandischema.models import hed_standard

    assert hed_standard["schemaKey"] == "StandardsType"
    assert hed_standard["name"] == "Hierarchical Event Descriptors (HED)"
    assert hed_standard["identifier"] == "RRID:SCR_014074"


def test_aggregate_per_asset_datastandard() -> None:
    """Per-asset dataStandard entries are collected into the summary."""
    from dandischema.models import hed_standard

    data = [
        {
            "schemaKey": "Asset",
            "schemaVersion": "0.6.0",
            "path": "dataset_description.json",
            "encodingFormat": "application/json",
            "contentSize": 512,
            "digest": {"dandi:dandi-etag": "abc123-1"},
            "dataStandard": [hed_standard],
        },
    ]
    summary = aggregate_assets_summary(data)
    assert hed_standard in summary["dataStandard"]
    # dataset_description.json also triggers BIDS via deprecated heuristic
    assert sum("BIDS" in s.get("name", "") for s in summary["dataStandard"]) == 1


def test_aggregate_per_asset_datastandard_no_duplication() -> None:
    """No duplication when a standard is declared both per-asset and via heuristic."""
    from dandischema.models import bids_standard

    data = [
        {
            "schemaKey": "Asset",
            "schemaVersion": "0.6.0",
            "path": "dataset_description.json",
            "encodingFormat": "application/json",
            "contentSize": 512,
            "digest": {"dandi:dandi-etag": "abc123-1"},
            "dataStandard": [bids_standard],
        },
    ]
    summary = aggregate_assets_summary(data)
    bids_count = sum("BIDS" in s.get("name", "") for s in summary["dataStandard"])
    assert bids_count == 1, "BIDS should appear exactly once, not duplicated"


class TestValidateObjJson:
    """
    Tests for `_validate_obj_json()`
    """

    @pytest.fixture
    def dummy_jvalidator(self) -> JsonschemaValidator:
        """Returns a dummy jsonschema validator initialized with a dummy schema."""
        return jsonschema_validator(
            {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            check_format=True,
        )

    @pytest.fixture
    def dummy_instance(self) -> dict:
        """Returns a dummy instance"""
        return {"name": "Example"}

    def test_valid_obj_no_errors(
        self,
        monkeypatch: pytest.MonkeyPatch,
        dummy_jvalidator: JsonschemaValidator,
        dummy_instance: dict,
    ) -> None:
        """
        Test that `_validate_obj_json` does not raise when `validate_json` has no errors
        """

        def mock_validate_json(_instance: dict, _schema: dict) -> None:
            """Simulate successful validation with no exceptions."""
            return  # No error raised

        # Patch the validate_json function used inside `_validate_obj_json`
        from dandischema import metadata

        monkeypatch.setattr(metadata, "validate_json", mock_validate_json)

        # `_validate_obj_json` should succeed without raising an exception
        _validate_obj_json(dummy_instance, dummy_jvalidator)

    def test_raises_error_without_missing_ok(
        self,
        monkeypatch: pytest.MonkeyPatch,
        dummy_jvalidator: JsonschemaValidator,
        dummy_instance: dict,
    ) -> None:
        """
        Test that `_validate_obj_json` forwards JsonschemaValidationError
        when `missing_ok=False`.
        """

        def mock_validate_json(_instance: dict, _schema: dict) -> None:
            """Simulate validation error."""
            # Create a mock error that says a field is invalid
            raise JsonschemaValidationError(
                errors=[MagicMock(message="`name` is a required property")]
            )

        from dandischema import metadata

        monkeypatch.setattr(metadata, "validate_json", mock_validate_json)

        # Since `missing_ok=False`, any error should be re-raised.
        with pytest.raises(JsonschemaValidationError) as excinfo:
            _validate_obj_json(dummy_instance, dummy_jvalidator, missing_ok=False)
        assert "`name` is a required property" == excinfo.value.errors[0].message

    @pytest.mark.parametrize(
        ("validation_errs", "expect_raises", "expected_remaining_errs_count"),
        [
            pytest.param(
                [
                    MagicMock(message="`name` is a required property"),
                    MagicMock(message="`title` is a required property ..."),
                ],
                False,
                None,
                id="no_remaining_errors",
            ),
            pytest.param(
                [
                    MagicMock(message="`name` is a required property"),
                    MagicMock(message="Some other validation error"),
                ],
                True,
                1,
                id="one_remaining_error",
            ),
        ],
    )
    def test_raises_only_nonmissing_errors_with_missing_ok(
        self,
        monkeypatch: pytest.MonkeyPatch,
        dummy_jvalidator: JsonschemaValidator,
        dummy_instance: dict,
        validation_errs: list[MagicMock],
        expect_raises: bool,
        expected_remaining_errs_count: Optional[int],
    ) -> None:
        """
        Test that `_validate_obj_json` filters out 'is a required property' errors
        when `missing_ok=True`.
        """

        def mock_validate_json(_instance: dict, _schema: dict) -> None:
            """
            Simulate multiple validation errors, including missing required property.
            """
            raise JsonschemaValidationError(
                errors=validation_errs  # type: ignore[arg-type]
            )

        from dandischema import metadata

        monkeypatch.setattr(metadata, "validate_json", mock_validate_json)

        # If expect_raises is True, we use pytest.raises(ValidationError)
        # Otherwise, we enter a no-op context
        ctx = (
            pytest.raises(JsonschemaValidationError) if expect_raises else nullcontext()
        )

        with ctx as excinfo:
            _validate_obj_json(dummy_instance, dummy_jvalidator, missing_ok=True)

        if excinfo is not None:
            filtered_errors = excinfo.value.errors

            # We expect the "required property" error to be filtered out,
            # so we should only see the "Some other validation error".
            assert len(filtered_errors) == expected_remaining_errs_count


class TestGetJsonschemaValidator:
    @pytest.mark.parametrize(
        "schema_version, schema_key, expected_error_msg",
        [
            pytest.param(
                "0.5.8",
                "Dandiset",
                "DANDI schema version 0.5.8 is not allowed",
                id="invalid-schema-version",
            ),
            pytest.param(
                "0.6.0",
                "Nonexistent",
                "Schema key must be one of",
                id="invalid-schema-key",
            ),
        ],
    )
    def test_invalid_parameters(
        self, schema_version: str, schema_key: str, expected_error_msg: str
    ) -> None:
        """
        Test that providing an invalid schema version or key raises ValueError.
        """
        # Clear the cache to avoid interference from previous calls
        _get_jsonschema_validator.cache_clear()
        with pytest.raises(ValueError, match=expected_error_msg):
            _get_jsonschema_validator(schema_version, schema_key)

    def test_valid_schema(self) -> None:
        """
        Test the valid case:
          - requests.get() is patched directly using patch("requests.get")
          - The returned JSON is a valid dict
          - The resulting validator is produced via dandi_jsonschema_validator
        """
        valid_version = "0.6.0"
        valid_key = "Dandiset"
        expected_url = (
            f"https://raw.githubusercontent.com/dandi/schema/master/releases/"
            f"{valid_version}/dandiset.json"
        )
        dummy_validator = MagicMock(spec=JsonschemaValidator)
        valid_schema = {"type": "object"}

        with patch("requests.get") as mock_get, patch(
            "dandischema.metadata.dandi_jsonschema_validator",
            return_value=dummy_validator,
        ) as mock_validator:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = valid_schema
            mock_get.return_value = mock_response

            # Clear the cache to avoid interference from previous calls
            _get_jsonschema_validator.cache_clear()
            result = _get_jsonschema_validator(valid_version, valid_key)

            mock_get.assert_called_once_with(expected_url)
            mock_response.raise_for_status.assert_called_once()
            mock_response.json.assert_called_once()
            mock_validator.assert_called_once_with(valid_schema)
            assert result is dummy_validator

    def test_invalid_json_schema_raises_runtime_error(self) -> None:
        """
        Test that if the fetched schema is not a valid JSON object,
        then _get_jsonschema_validator() raises a RuntimeError.
        """
        valid_version = "0.6.0"
        valid_key = "Dandiset"
        expected_url = (
            f"https://raw.githubusercontent.com/dandi/schema/master/releases/"
            f"{valid_version}/dandiset.json"
        )
        # Return a list (instead of a dict) to trigger a ValidationError in json_object_adapter
        invalid_schema = {4: 2}

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = invalid_schema
            mock_get.return_value = mock_response

            # Clear the cache to avoid interference from previous calls
            _get_jsonschema_validator.cache_clear()
            with pytest.raises(RuntimeError, match="not a valid JSON object"):
                _get_jsonschema_validator(valid_version, valid_key)

            mock_get.assert_called_once_with(expected_url)
            mock_response.raise_for_status.assert_called_once()
            mock_response.json.assert_called_once()


class TestGetJsonschemaValidatorLocal:
    @pytest.mark.parametrize(
        ("schema_key", "pydantic_model"),
        [
            pytest.param("Dandiset", Dandiset, id="valid-Dandiset"),
            pytest.param(
                "PublishedDandiset", PublishedDandiset, id="valid-PublishedDandiset"
            ),
            pytest.param("Asset", Asset, id="valid-Asset"),
            pytest.param("PublishedAsset", PublishedAsset, id="valid-PublishedAsset"),
        ],
    )
    def test_valid_schema_keys(
        self, schema_key: str, pydantic_model: type[BaseModel]
    ) -> None:
        # Get the expected schema from the corresponding model.
        expected_schema = pydantic_model.model_json_schema(
            schema_generator=TransitionalGenerateJsonSchema
        )

        # Clear the cache to avoid interference from previous calls
        _get_jsonschema_validator_local.cache_clear()

        # Call the function under test.
        validator = _get_jsonschema_validator_local(schema_key)

        # Assert that the returned validator has a 'schema' attribute
        # equal to the expected schema.
        assert validator.schema == expected_schema, (
            f"For schema key {schema_key!r}, expected schema:\n{expected_schema}\n"
            f"but got:\n{validator.schema}"
        )

    @pytest.mark.parametrize(
        "invalid_schema_key",
        [
            pytest.param("Nonexistent", id="invalid-Nonexistent"),
            pytest.param("", id="invalid-empty-string"),
            pytest.param("InvalidKey", id="invalid-Key"),
        ],
    )
    def test_invalid_schema_keys(self, invalid_schema_key: str) -> None:
        # Clear the cache to avoid interference from previous calls
        _get_jsonschema_validator_local.cache_clear()

        with pytest.raises(ValueError, match="Schema key must be one of"):
            _get_jsonschema_validator_local(invalid_schema_key)
