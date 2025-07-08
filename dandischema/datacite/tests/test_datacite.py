from copy import deepcopy
import json
import os
from pathlib import Path
import random
from typing import Any, Dict, Tuple

from jsonschema import Draft7Validator
import pytest
import requests

from dandischema.models import (
    Dandiset,
    LicenseType,
    PublishedDandiset,
    RelationType,
    ResourceType,
    RoleType,
)
import dandischema.tests
from dandischema.tests.utils import _basic_publishmeta, skipif_no_network

from .. import _get_datacite_schema, to_datacite


def datacite_post(datacite: dict, doi: str, clean: bool = True) -> None:
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
    print("\n in datacite_post, after posting", doi, rp.status_code)
    # checking if i'm able to get the url
    rg = requests.get(url=f"https://api.test.datacite.org/dois/{doi}/activities")
    rg.raise_for_status()

    if clean:
        # cleaning url
        _clean_doi(doi)


def datacite_update(datacite: dict, doi: str) -> None:
    """Update the datacite object and check the status of the request"""
    rp = requests.put(
        url=f"https://api.test.datacite.org/dois/{doi}",
        json=datacite,
        headers={"Content-Type": "application/vnd.api+json"},
        auth=("DARTLIB.DANDI", os.environ["DATACITE_DEV_PASSWORD"]),
    )
    rp.raise_for_status()

    # checking if i'm able to get the url
    rg = requests.get(url=f"https://api.test.datacite.org/dois/{doi}/activities")
    rg.raise_for_status()


def _clean_doi(doi: str) -> None:
    """Remove doi. Status code is ignored"""
    rq = requests.delete(
        f"https://api.test.datacite.org/dois/{doi}",
        auth=("DARTLIB.DANDI", os.environ["DATACITE_DEV_PASSWORD"]),
    )
    print("\n in _clean_doi", doi, rq.status_code)
    return rq.status_code


@pytest.mark.skip(
    reason="to not produced too many dois, not sure if we want to keep it as a test"
)
def test_datacite_lifecycle() -> None:
    """testing the lifecycle of a public dandiset and doi (from draft to published)"""

    # checking which doi is available
    doi_available = False
    while not doi_available:
        dandi_id = f"000{random.randrange(500, 999)}"
        print(f"searching for available doi, trying dandi_id: {dandi_id}")
        doi_root = f"10.80507/dandi.{dandi_id}"
        if _clean_doi(doi_root) != 405:
            doi_available = True
            print(f"found available doi, dandi_id: {dandi_id}")

    dandi_id_prefix = f"DANDI:{dandi_id}"
    # creating the main/root doi and url
    doi_root = f"10.80507/dandi.{dandi_id}"
    url_root = f"https://dandiarchive.org/dandiset/{dandi_id}"

    # creating draft dandiset with minimal metadata
    version = "draft"
    meta_dict = {
        "identifier": dandi_id_prefix,
        "id": f"{dandi_id_prefix}/{version}",
        "name": "Testing Dataset: lifecycle",
        "description": "testing lifecycle of a dataset and doi: draft",
        "version": version,
        "contributor": [
            {
                "name": "A_last, A_first",
                "email": "nemo@example.com",
                "roleName": [RoleType("dcite:ContactPerson")],
                "schemaKey": "Person",
            }
        ],
        "license": [LicenseType("spdx:CC-BY-4.0")],
        "citation": "A_last, A_first 2021",
        "manifestLocation": [
            f"https://api.dandiarchive.org/api/dandisets/{dandi_id}/versions/{version}/assets/"
        ],
        "assetsSummary": {
            "schemaKey": "AssetsSummary",
            "numberOfBytes": 10,
            "numberOfFiles": 1,
        },
    }
    # in addition to minimal metadata, we need to add doi and url if we want to create draft doi
    meta_dict["doi"] = doi_root
    meta_dict["url"] = url_root
    # creating draft dandiset
    dset = Dandiset(**meta_dict)

    # creating datacite object and posting the main doi entry (should be draft)
    datacite = to_datacite(dset)
    datacite_post(datacite, doi_root, clean=False)

    # updating the draft but not enough to create PublishDandiset
    meta_dict["description"] = "testing lifecycle of a dataset and doi: new draft"
    # the dandi workflow should check if we cna create a datacite that can be validated and published
    # try: datacite_new = to_datacite(meta_dict, validate=True, publish=True)
    # if the metadata is not enough to create a valid datacite, we should update the draft doi
    datacite_new = to_datacite(meta_dict)
    datacite_update(datacite_new, doi_root)

    # creating v1.0.0
    version = "1.0.0"
    # adding contributors and updating description
    meta_dict["contributor"].append(
        {
            "name": "B_last, B_first",
            "email": "nemo@example.com",
            "roleName": [RoleType("dcite:DataCurator")],
            "schemaKey": "Person",
        }
    )
    meta_dict["description"] = "testing lifecycle of a dataset and doi: v1.0.0"
    # adding mandatory metadata for PublishDandiset
    publish_meta = {
        "datePublished": "2020",
        "publishedBy": {
            "id": "urn:uuid:08fffc59-9f1b-44d6-8e02-6729d266d1b6",
            "name": "DANDI publish",
            "startDate": "2021-05-18T19:58:39.310338-04:00",
            "endDate": "2021-05-18T19:58:39.310361-04:00",
            "wasAssociatedWith": [
                {
                    "id": "urn:uuid:9267d2e1-4a37-463b-9b10-dad3c66d8eaa",
                    "identifier": "RRID:SCR_017571",
                    "name": "DANDI API",
                    "version": version,
                    "schemaKey": "Software",
                }
            ],
            "schemaKey": "PublishActivity",
        },
    }
    meta_dict.update(publish_meta)
    # updating the version, id etc.
    meta_dict["version"] = version
    meta_dict["id"] = f"{dandi_id_prefix}/{version}"
    meta_dict["doi"] = f"{doi_root}/{version}"
    meta_dict["url"] = f"https://dandiarchive.org/dandiset/{dandi_id}/{version}"
    # creating new published dandiset
    dset_v1 = PublishedDandiset(**meta_dict)
    # creating datacite object and posting (should be findable)
    datacite_v1 = to_datacite(dset_v1, publish=True, validate=True)
    datacite_post(datacite_v1, meta_dict["doi"], clean=False)

    # updating the main doi but keeping the root doi and url
    datacite = deepcopy(datacite_v1)
    datacite["data"]["attributes"]["doi"] = doi_root
    datacite["data"]["attributes"]["url"] = url_root
    # updating the doi (should change from draft to findable)
    datacite_update(datacite, doi_root)

    # creating v2.0.0
    version = "2.0.0"
    # updating description
    meta_dict["description"] = "testing lifecycle of a dataset and doi: v2.0.0"
    meta_dict["version"] = version
    meta_dict["id"] = f"{dandi_id_prefix}/{version}"
    meta_dict["doi"] = f"{doi_root}/{version}"
    meta_dict["url"] = f"https://dandiarchive.org/dandiset/{dandi_id}/{version}"
    # creating new published dandiset
    dset_v2 = PublishedDandiset(**meta_dict)
    # creating datacite object and posting (should be findable)
    datacite_v2 = to_datacite(dset_v2, publish=True, validate=True)
    datacite_post(datacite_v2, meta_dict["doi"], clean=False)

    # updating the main doi to v2 but keeping the root doi and url
    datacite = deepcopy(datacite_v2)
    datacite["data"]["attributes"]["doi"] = doi_root
    datacite["data"]["attributes"]["url"] = url_root
    # updating the findable doi
    datacite_update(datacite, doi_root)


@pytest.fixture(scope="module")
def schema() -> Any:
    return _get_datacite_schema()


@pytest.fixture(scope="function")
def metadata_basic() -> Dict[str, Any]:
    dandi_id_noprefix = f"000{random.randrange(100, 499)}"
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
        "assetsSummary": {
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
        },
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
    metadata_basic: Dict[str, Any],
    additional_meta: Dict[str, Any],
    datacite_checks: Dict[str, Any],
) -> None:
    """
    checking datacite objects for specific metadata dictionaries,
    posting datacite object and checking the status code
    """

    dandi_id = metadata_basic["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]

    metadata_basic.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))
    metadata_basic.update(additional_meta)

    # creating and validating datacite objects
    datacite = to_datacite(metadata_basic)
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
    datacite_post(datacite, metadata_basic["doi"])


def test_datacite_publish(metadata_basic: Dict[str, Any]) -> None:
    dandi_id = metadata_basic["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    version = metadata_basic["version"]
    metadata_basic.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    # creating and validating datacite objects
    datacite = to_datacite(metadata_basic, publish=True, validate=True)

    assert datacite == {
        # 'data': {}
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
                "publicationYear": "1970",
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
    metadata_basic: Dict[str, Any],
    related_res_url: Dict[str, Any],
    related_ident_exp: Tuple[str, str],
) -> None:
    """
    checking if urls provided in the relatedResource.identifier could be
    translated to DOI for some websites: e.g. bioarxiv.org, doi.org
    """
    dandi_id = metadata_basic["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]

    metadata_basic.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))
    metadata_basic["relatedResource"] = [related_res_url]

    # creating and validating datacite objects
    datacite = to_datacite(metadata_basic)
    relIdent = datacite["data"]["attributes"]["relatedIdentifiers"][0]
    assert relIdent["relatedIdentifier"] == related_ident_exp[0].lower()
    assert relIdent["relatedIdentifierType"] == related_ident_exp[1]
