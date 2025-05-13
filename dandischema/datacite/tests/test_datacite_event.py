import random
from copy import deepcopy
from typing import Dict, Any

import pytest

from dandischema.models import LicenseType, RoleType
from dandischema.tests.utils import _basic_publishmeta
from dandischema.datacite import to_datacite


@pytest.fixture(scope="function")
def metadata_basic_event() -> Dict[str, Any]:
    """Create a basic metadata dictionary for testing DOI generation"""
    dandi_id_noprefix = f"000{random.randrange(100, 999)}"
    dandi_id = f"DANDI:{dandi_id_noprefix}"
    version = "0.0.0"

    # Create metadata similar to what's used in test_datacite.py
    meta_dict = {
        "identifier": dandi_id,
        "id": f"{dandi_id}/{version}",
        "name": "testing dataset",
        "description": "testing",
        "contributor": [
            {
                "name": "A_last, A_first",
                "email": "nemo@example.com",
                "roleName": [RoleType("dcite:ContactPerson")],
                "schemaKey": "Person",
            }
        ],
        "license": [LicenseType("spdx:CC-BY-4.0")],
        "url": f"https://dandiarchive.org/dandiset/{dandi_id_noprefix}/{version}",
        "version": version,
        "citation": "A_last, A_first 2021",
        "manifestLocation": [
            f"https://api.dandiarchive.org/api/dandisets/{dandi_id_noprefix}/versions/draft/assets/"
        ],
        "assetsSummary": {
            "schemaKey": "AssetsSummary",
            "numberOfBytes": 10,
            "numberOfFiles": 1,
            "dataStandard": [{"schemaKey": "StandardsType", "name": "NWB"}],
        },
    }

    return meta_dict


def test_event_none_draft_doi(metadata_basic_event: Dict[str, Any]) -> None:
    """Test that event=None creates a Draft DOI (no event in payload)"""
    dandi_id = metadata_basic_event["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    metadata_basic_event.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    datacite = to_datacite(metadata_basic_event, event=None)

    # Check that there is no event attribute
    assert "event" not in datacite["data"]["attributes"]


def test_no_event_draft_doi(metadata_basic_event: Dict[str, Any]) -> None:
    """Test that event=None creates a Draft DOI (no event in payload)"""
    dandi_id = metadata_basic_event["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    metadata_basic_event.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    datacite = to_datacite(metadata_basic_event)

    # Check that there is no event attribute
    assert "event" not in datacite["data"]["attributes"]


def test_event_publish_findable_doi(metadata_basic_event: Dict[str, Any]) -> None:
    """Test that event="publish" creates a Findable DOI"""
    dandi_id = metadata_basic_event["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    metadata_basic_event.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    datacite = to_datacite(metadata_basic_event, event="publish")

    # Check that event is "publish"
    assert datacite["data"]["attributes"]["event"] == "publish"


def test_event_hide_registered_doi(metadata_basic_event: Dict[str, Any]) -> None:
    """Test that event="hide" creates a Registered DOI"""
    dandi_id = metadata_basic_event["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    metadata_basic_event.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    datacite = to_datacite(metadata_basic_event, event="hide")

    # Check that event is "hide"
    assert datacite["data"]["attributes"]["event"] == "hide"


def test_invalid_event(metadata_basic_event: Dict[str, Any]) -> None:
    """Test that invalid event values raise ValueError"""
    dandi_id = metadata_basic_event["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    metadata_basic_event.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    with pytest.raises(ValueError, match="Invalid event value"):
        to_datacite(metadata_basic_event, event="invalid")


def test_event_and_publish_conflict(metadata_basic_event: Dict[str, Any]) -> None:
    """Test that using both event and publish parameters raises ValueError"""
    dandi_id = metadata_basic_event["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    metadata_basic_event.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    with pytest.raises(ValueError, match="Cannot use both 'event' and deprecated 'publish'"):
        to_datacite(metadata_basic_event, event="publish", publish=True)


def test_deprecated_publish_parameter(metadata_basic_event: Dict[str, Any]) -> None:
    """Test the deprecated publish parameter still works but shows warning"""
    dandi_id = metadata_basic_event["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    metadata_basic_event.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    with pytest.warns(DeprecationWarning, match="'publish' is deprecated"):
        datacite = to_datacite(metadata_basic_event, publish=True)

    # Check that event is "publish" despite using the deprecated parameter
    assert datacite["data"]["attributes"]["event"] == "publish"


def test_dandiset_doi_url_handling(metadata_basic_event: Dict[str, Any]) -> None:
    """Test that a Dandiset DOI points to the DLP (no version in URL)"""
    dandi_id = metadata_basic_event["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    version = metadata_basic_event["version"]

    # Create a copy of the metadata
    meta_dict = deepcopy(metadata_basic_event)
    meta_dict.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    # Override with a Dandiset DOI (no version)
    meta_dict["doi"] = f"10.80507/dandi.{dandi_id_noprefix}"

    # Process as a Dandiset DOI
    datacite = to_datacite(meta_dict)

    # Verify the DOI is correctly reflected in output
    assert datacite["data"]["attributes"]["doi"] == meta_dict["doi"]

    # Verify that the URL in the metadata contains the version ID
    assert f"/{version}" in meta_dict["url"]

    # And the URL in the datacite output should use the same URL
    assert datacite["data"]["attributes"]["url"] == meta_dict["url"]


def test_doi_formats(metadata_basic_event: Dict[str, Any]) -> None:
    """Test both Dandiset DOI and Version DOI format handling"""
    dandi_id = metadata_basic_event["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    version = metadata_basic_event["version"]

    # Test with Dandiset DOI format
    dandiset_meta = deepcopy(metadata_basic_event)
    dandiset_meta.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))
    dandiset_meta["doi"] = f"10.80507/dandi.{dandi_id_noprefix}"
    dandiset_datacite = to_datacite(dandiset_meta)

    # Test with Version DOI format
    version_meta = deepcopy(metadata_basic_event)
    version_meta.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))
    version_meta["doi"] = f"10.80507/dandi.{dandi_id_noprefix}/{version}"
    version_datacite = to_datacite(version_meta)

    # Verify DOIs are correctly reflected in output
    assert dandiset_datacite["data"]["attributes"]["doi"] == dandiset_meta["doi"]
    assert version_datacite["data"]["attributes"]["doi"] == version_meta["doi"]
