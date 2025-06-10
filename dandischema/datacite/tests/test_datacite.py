from copy import deepcopy
from datetime import datetime
import json
import os
from pathlib import Path
import random
from typing import Any, Dict, Tuple

from jsonschema import Draft7Validator
import pytest
import requests

from dandischema.models import (
    LicenseType,
    PublishedDandiset,
    RelationType,
    ResourceType,
    RoleType,
)
import dandischema.tests
from dandischema.tests.utils import _basic_publishmeta, skipif_no_network

from .. import _get_datacite_schema, to_datacite


def datacite_post(datacite: dict, doi: str) -> None:
    """Post the datacite object and check the status of the request"""

    # removing doi in case it exists
    _clean_doi(doi)

    # checking f I'm able to create doi
    rp = requests.post(
        "https://api.test.datacite.org/dois",
        json=datacite,
        headers={"Content-Type": "application/vnd.api+json"},
        auth=("DARTLIB.DANDI", os.environ["DATACITE_DEV_PASSWORD"]),
    )
    rp.raise_for_status()

    # checking if i'm able to get the url
    rg = requests.get(url=f"https://api.test.datacite.org/dois/{doi}/activities")
    rg.raise_for_status()

    # cleaning url
    _clean_doi(doi)


def _clean_doi(doi: str) -> None:
    """Remove doi. Status code is ignored"""
    requests.delete(
        f"https://api.test.datacite.org/dois/{doi}",
        auth=("DARTLIB.DANDI", os.environ["DATACITE_DEV_PASSWORD"]),
    )


@pytest.fixture(scope="module")
def schema() -> Any:
    return _get_datacite_schema()


@pytest.fixture(scope="function")
def metadata_minimal() -> Dict[str, Any]:
    """Basic metadata without assetsSummary"""
    dandi_id_noprefix = f"000{random.randrange(100, 999)}"
    dandi_id = f"DANDI:{dandi_id_noprefix}"
    version = "0.0.0"
    # meta data without doi, datePublished and publishedBy
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
    }

    return meta_dict


@pytest.fixture(scope="function")
def metadata_with_assets(metadata_minimal: Dict[str, Any]) -> Dict[str, Any]:
    """Metadata with assetsSummary included"""
    meta_dict = deepcopy(metadata_minimal)
    meta_dict["assetsSummary"] = {
        "schemaKey": "AssetsSummary",
        "numberOfBytes": 10,
        "numberOfFiles": 1,
        "dataStandard": [{"schemaKey": "StandardsType", "name": "NWB"}],
        "approach": [{"schemaKey": "ApproachType", "name": "electrophysiology"}],
        "measurementTechnique": [
            {
                "schemaKey": "MeasurementTechniqueType",
                "name": "two-photon microscopy technique",
            }
        ],
        "species": [{"schemaKey": "SpeciesType", "name": "Human"}],
    }
    return meta_dict



@skipif_no_network
@pytest.mark.skipif(
    not os.getenv("DATACITE_DEV_PASSWORD"), reason="no datacite password available"
)
@pytest.mark.parametrize("dandi_id", ["000004", "000008"])
def test_datacite(dandi_id: str, schema: Any) -> None:
    """checking to_datacite for a specific datasets"""

    # reading metadata taken from exemplary dandisets and saved in json files
    with (
        Path(dandischema.tests.__file__).with_name("data")
        / "metadata"
        / f"meta_{dandi_id}.json"
    ).open() as f:
        meta_js = json.load(f)

    version = "0.0.0"
    meta_js["id"] = meta_js["id"].replace(meta_js["version"], version)
    meta_js["url"] = meta_js["url"].replace(meta_js["version"], version)
    meta_js["version"] = version

    # updating with basic fields required for PublishDandiset
    meta_js.update(
        _basic_publishmeta(dandi_id.replace("000", str(random.randrange(100, 999))))
    )
    meta = PublishedDandiset(**meta_js)

    datacite = to_datacite(meta=meta, validate=True)

    # trying to post datacite
    datacite_post(datacite, meta.doi)


@pytest.mark.flaky(reruns=5, reruns_delay=5, only_rerun="HTTPError")
@skipif_no_network
@pytest.mark.parametrize(
    "additional_meta, datacite_checks",
    [
        # no additional meta
        (
            {},
            {
                "creators": (1, {"name": "A_last, A_first"}),
                "titles": (1, {"title": "testing dataset"}),
                "descriptions": (
                    1,
                    {"description": "testing", "descriptionType": "Abstract"},
                ),
                "publisher": (
                    None,
                    {
                        "name": "DANDI Archive",
                        "publisherIdentifier": "https://scicrunch.org/resolver/RRID:SCR_017571",
                        "publisherIdentifierScheme": "RRID",
                        "schemeUri": "https://scicrunch.org/resolver/",
                        "lang": "en",
                    },
                ),
                "rightsList": (
                    1,
                    {"rightsIdentifierScheme": "SPDX", "rightsIdentifier": "CC_BY_40"},
                ),
                "types": (
                    None,
                    {"resourceType": "Neural Data", "resourceTypeGeneral": "Dataset"},
                ),
            },
        ),
        # additional contributor with dandi:Author, and one without roleName
        (
            {
                "contributor": [
                    {
                        "name": "A_last, A_first",
                        "roleName": [RoleType("dcite:ContactPerson")],
                        "email": "nemo@example.com",
                        "schemaKey": "Person",
                    },
                    {
                        "name": "B_last, B_first",
                        "roleName": [RoleType("dcite:Author")],
                        "schemaKey": "Person",
                    },
                    {
                        "name": "C_last, C_first",
                        "schemaKey": "Person",
                    },
                ],
            },
            {
                "creators": (1, {"name": "B_last, B_first"}),
                "contributors": (
                    2,
                    {"name": "A_last, A_first", "contributorType": "ContactPerson"},
                ),
            },
        ),
        # additional contributor with dandi:Sponsor, fundingReferences should be created
        (
            {
                "contributor": [
                    {
                        "name": "A_last, A_first",
                        "roleName": [RoleType("dcite:ContactPerson")],
                        "email": "nemo@example.com",
                        "schemaKey": "Person",
                    },
                    {
                        "name": "B_last, B_first",
                        "roleName": [RoleType("dcite:Sponsor")],
                        "schemaKey": "Person",
                    },
                ],
            },
            {
                "creators": (1, {"name": "A_last, A_first"}),
                "fundingReferences": (1, {"funderName": "B_last, B_first"}),
            },
        ),
        # Add a sponsor with an identifier
        (
            {
                "contributor": [
                    {
                        "name": "A_last, A_first",
                        "roleName": [RoleType("dcite:ContactPerson")],
                        "email": "nemo@example.com",
                        "schemaKey": "Person",
                    },
                    {
                        "name": "B_last, B_first",
                        "identifier": "0000-0001-0000-0000",
                        "roleName": [RoleType("dcite:Sponsor")],
                        "schemaKey": "Person",
                    },
                ],
            },
            {
                "creators": (1, {"name": "A_last, A_first"}),
                "fundingReferences": (
                    1,
                    {
                        "funderName": "B_last, B_first",
                        "funderIdentifier": "0000-0001-0000-0000",
                        "funderIdentifierType": "Other",
                    },
                ),
            },
        ),
        # should also work with Funder role
        (
            {
                "contributor": [
                    {
                        "name": "A_last, A_first",
                        "roleName": [RoleType("dcite:ContactPerson")],
                        "email": "nemo@example.com",
                        "schemaKey": "Person",
                    },
                    {
                        "name": "B_last, B_first",
                        "identifier": "0000-0001-0000-0000",
                        "roleName": [RoleType("dcite:Funder")],
                        "schemaKey": "Person",
                    },
                ],
            },
            {
                "creators": (1, {"name": "A_last, A_first"}),
                "fundingReferences": (
                    1,
                    {
                        "funderName": "B_last, B_first",
                        "funderIdentifier": "0000-0001-0000-0000",
                        "funderIdentifierType": "Other",
                    },
                ),
            },
        ),
        # additional contributor with 2 roles: Author and Software (doesn't exist in datacite)
        # the person should be in creators and contributors (with contributorType Other)
        # Adding Orcid ID to the identifier to one of the contributors
        (
            {
                "contributor": [
                    {
                        "name": "A_last, A_first",
                        "roleName": [
                            RoleType("dcite:Author"),
                            RoleType("dcite:Software"),
                        ],
                        "identifier": "0000-0001-0000-0000",
                        "schemaKey": "Person",
                    },
                    {
                        "name": "B_last, B_first",
                        "roleName": [RoleType("dcite:ContactPerson")],
                        "email": "nemo@example.com",
                        "schemaKey": "Person",
                    },
                ],
            },
            {
                "creators": (
                    1,
                    {
                        "name": "A_last, A_first",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "https://orcid.org/0000-0001-0000-0000",
                                "nameIdentifierScheme": "ORCID",
                                "schemeUri": "https://orcid.org/",
                            }
                        ],
                    },
                ),
                "contributors": (
                    2,
                    {
                        "name": "A_last, A_first",
                        "contributorType": "Other",
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "https://orcid.org/0000-0001-0000-0000",
                                "nameIdentifierScheme": "ORCID",
                                "schemeUri": "https://orcid.org/",
                            }
                        ],
                    },
                ),
            },
        ),
        (
            {
                "relatedResource": [
                    {
                        "url": "https://github.com/org/project",
                        "relation": RelationType("dcite:IsSupplementedBy"),
                    },
                    {
                        "identifier": "doi:10.123/123",
                        "relation": RelationType("dcite:IsDocumentedBy"),
                        "resourceType": ResourceType("dcite:JournalArticle"),
                    },
                ],
            },
            {
                "relatedIdentifiers": (
                    2,
                    {
                        "relatedIdentifier": "https://github.com/org/project",
                        "relatedIdentifierType": "URL",
                        "relationType": "IsSupplementedBy",
                    },
                ),
            },
        ),
    ],
)
@pytest.mark.skipif(
    not os.getenv("DATACITE_DEV_PASSWORD"), reason="no datacite password available"
)
def test_dandimeta_datacite(
    schema: Any,
    metadata_with_assets: Dict[str, Any],
    additional_meta: Dict[str, Any],
    datacite_checks: Dict[str, Any],
) -> None:
    """
    checking datacite objects for specific metadata dictionaries,
    posting datacite object and checking the status code
    """

    dandi_id = metadata_with_assets["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]

    metadata_with_assets.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))
    metadata_with_assets.update(additional_meta)

    # creating and validating datacite objects
    datacite = to_datacite(metadata_with_assets)
    Draft7Validator.check_schema(schema)
    validator = Draft7Validator(schema)
    validator.validate(datacite["data"]["attributes"])

    # checking some datacite fields
    attr = datacite["data"]["attributes"]
    for key, el in datacite_checks.items():
        el_len, el_flds = el
        if el_len:
            # checking length and some fields from the first element
            assert len(attr[key]) == el_len
            for k, v in el_flds.items():
                assert attr[key][0][k] == v
        else:
            if isinstance(el_flds, dict):
                for k, v in el_flds.items():
                    assert attr[key][k] == v
            else:
                assert attr[key] == el_flds

    # trying to post to datacite
    datacite_post(datacite, metadata_with_assets["doi"])


def test_datacite_publish(metadata_with_assets: Dict[str, Any]) -> None:
    dandi_id = metadata_with_assets["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    version = metadata_with_assets["version"]
    metadata_with_assets.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    # creating and validating datacite objects
    with pytest.warns(DeprecationWarning, match="'publish' is deprecated"):
        datacite = to_datacite(metadata_with_assets, publish=True, validate=True)

    expected = {
        "data": {
            "id": f"10.80507/dandi.{dandi_id_noprefix}/{version}",
            "type": "dois",
            "attributes": {
                "event": "publish",
                "contributors": [
                    {
                        "affiliation": [],
                        "contributorName": "A_last, A_first",
                        "contributorType": "ContactPerson",
                        "familyName": "A_last",
                        "givenName": "A_first",
                        "name": "A_last, A_first",
                        "nameType": "Personal",
                        "schemeUri": "orcid.org",
                    }
                ],
                "creators": [
                    {
                        "affiliation": [],
                        "creatorName": "A_last, A_first",
                        "familyName": "A_last",
                        "givenName": "A_first",
                        "name": "A_last, A_first",
                        "nameType": "Personal",
                        "schemeUri": "orcid.org",
                    }
                ],
                "descriptions": [
                    {"description": "testing", "descriptionType": "Abstract"}
                ],
                "doi": f"10.80507/dandi.{dandi_id_noprefix}/{version}",
                "alternateIdentifiers": [
                    {
                        "alternateIdentifier": f"https://identifiers.org/{dandi_id}/{version}",
                        "alternateIdentifierType": "URL",
                    },
                    {
                        "alternateIdentifier": (
                            f"https://dandiarchive.org/dandiset"
                            f"/{dandi_id_noprefix}/{version}"
                        ),
                        "alternateIdentifierType": "URL",
                    },
                ],
                "publicationYear": str(datetime.now().year),
                "publisher": {
                    "name": "DANDI Archive",
                    "publisherIdentifier": "https://scicrunch.org/resolver/RRID:SCR_017571",
                    "publisherIdentifierScheme": "RRID",
                    "schemeUri": "https://scicrunch.org/resolver/",
                    "lang": "en",
                },
                "rightsList": [
                    {
                        "rightsIdentifier": "CC_BY_40",
                        "rightsIdentifierScheme": "SPDX",
                        "schemeUri": "https://spdx.org/licenses/",
                    }
                ],
                "schemaVersion": "http://datacite.org/schema/kernel-4",
                "titles": [{"title": "testing dataset"}],
                "types": {
                    "resourceType": "Neural Data",
                    "resourceTypeGeneral": "Dataset",
                },
                "url": f"https://dandiarchive.org/dandiset/{dandi_id_noprefix}/{version}",
                "version": version,
            },
        }
    }
    assert datacite == expected


@pytest.mark.parametrize(
    "related_res_url, related_ident_exp",
    [
        (
            {
                "identifier": "https://doi.org/10.1101/2021.04.26.441423",
                "relation": RelationType("dcite:IsSupplementedBy"),
            },
            ("10.1101/2021.04.26.441423", "DOI"),
        ),
        # identifier without https
        (
            {
                "identifier": "doi.org/10.1101/2021.04.26.441423",
                "relation": RelationType("dcite:IsSupplementedBy"),
            },
            ("10.1101/2021.04.26.441423", "DOI"),
        ),
        (
            {
                "identifier": "https://www.biorxiv.org/content/10.1101/2021.04.26.441423v2",
                "relation": RelationType("dcite:IsSupplementedBy"),
            },
            ("10.1101/2021.04.26.441423", "DOI"),
        ),
        # osf should stay as an url
        (
            {
                "identifier": "https://osf.io/n35zy/",
                "relation": RelationType("dcite:IsSupplementedBy"),
            },
            ("https://osf.io/n35zy/", "URL"),
        ),
    ],
)
@pytest.mark.skipif(
    not os.getenv("DATACITE_DEV_PASSWORD"), reason="no datacite password available"
)
def test_datacite_related_res_url(
    metadata_with_assets: Dict[str, Any],
    related_res_url: Dict[str, Any],
    related_ident_exp: Tuple[str, str],
) -> None:
    """
    checking if urls provided in the relatedResource.identifier could be
    translated to DOI for some websites: e.g. bioarxiv.org, doi.org
    """
    dandi_id = metadata_with_assets["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]

    metadata_with_assets.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))
    metadata_with_assets["relatedResource"] = [related_res_url]

    # creating and validating datacite objects
    datacite = to_datacite(metadata_with_assets)
    relIdent = datacite["data"]["attributes"]["relatedIdentifiers"][0]
    assert relIdent["relatedIdentifier"] == related_ident_exp[0].lower()
    assert relIdent["relatedIdentifierType"] == related_ident_exp[1]


def test_event_none_draft_doi(metadata_minimal: Dict[str, Any]) -> None:
    """Test that event=None leaves event out of payload)"""
    dandi_id = metadata_minimal["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    metadata_minimal.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    datacite = to_datacite(metadata_minimal, event=None)

    # Check that there is no event attribute
    assert "event" not in datacite["data"]["attributes"]


def test_no_event_draft_doi(metadata_minimal: Dict[str, Any]) -> None:
    """Test that event is optional (no event in payload)"""
    dandi_id = metadata_minimal["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    metadata_minimal.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    datacite = to_datacite(metadata_minimal)

    # Check that there is no event attribute
    assert "event" not in datacite["data"]["attributes"]


def test_event_publish_findable_doi(metadata_minimal: Dict[str, Any]) -> None:
    """Test that event="publish" is included in payload"""
    dandi_id = metadata_minimal["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    metadata_minimal.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    datacite = to_datacite(metadata_minimal, event="publish")

    # Check that event is "publish"
    assert datacite["data"]["attributes"]["event"] == "publish"


def test_event_hide_registered_doi(metadata_minimal: Dict[str, Any]) -> None:
    """Test that event="hide" is included in payload"""
    dandi_id = metadata_minimal["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    metadata_minimal.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    datacite = to_datacite(metadata_minimal, event="hide")

    # Check that event is "hide"
    assert datacite["data"]["attributes"]["event"] == "hide"


def test_invalid_event(metadata_minimal: Dict[str, Any]) -> None:
    """Test that invalid event values raise ValueError"""
    dandi_id = metadata_minimal["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    metadata_minimal.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    with pytest.raises(ValueError, match="Invalid event value"):
        to_datacite(metadata_minimal, event="invalid")


def test_event_and_publish_conflict(metadata_minimal: Dict[str, Any]) -> None:
    """Test that using both event and publish parameters raises ValueError"""
    dandi_id = metadata_minimal["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    metadata_minimal.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    with pytest.raises(
        ValueError, match="Cannot use both 'event' and deprecated 'publish'"
    ):
        to_datacite(metadata_minimal, event="publish", publish=True)


def test_deprecated_publish_parameter(metadata_minimal: Dict[str, Any]) -> None:
    """Test the deprecated publish parameter still works but shows warning"""
    dandi_id = metadata_minimal["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    metadata_minimal.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    with pytest.warns(DeprecationWarning, match="'publish' is deprecated"):
        datacite = to_datacite(metadata_minimal, publish=True)

    # Check that event is "publish" despite using the deprecated parameter
    assert datacite["data"]["attributes"]["event"] == "publish"


def test_dandiset_doi_url_handling(metadata_minimal: Dict[str, Any]) -> None:
    """Test that a Dandiset DOI points to the DLP (no version in URL)"""
    dandi_id = metadata_minimal["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    version = metadata_minimal["version"]

    # Create a copy of the metadata
    meta_dict = deepcopy(metadata_minimal)
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


def test_doi_formats(metadata_minimal: Dict[str, Any]) -> None:
    """Test both Dandiset DOI and Version DOI format handling"""
    dandi_id = metadata_minimal["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    version = metadata_minimal["version"]

    # Test with Dandiset DOI format
    dandiset_meta = deepcopy(metadata_minimal)
    dandiset_meta.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))
    dandiset_meta["doi"] = f"10.80507/dandi.{dandi_id_noprefix}"
    dandiset_datacite = to_datacite(dandiset_meta)

    # Test with Version DOI format
    version_meta = deepcopy(metadata_minimal)
    version_meta.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))
    version_meta["doi"] = f"10.80507/dandi.{dandi_id_noprefix}/{version}"
    version_datacite = to_datacite(version_meta)

    # Verify DOIs are correctly reflected in output
    assert dandiset_datacite["data"]["attributes"]["doi"] == dandiset_meta["doi"]
    assert version_datacite["data"]["attributes"]["doi"] == version_meta["doi"]
