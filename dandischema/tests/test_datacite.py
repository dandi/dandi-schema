from datetime import datetime
import json
import os
from pathlib import Path
import random

from jsonschema import Draft7Validator
import pytest
import requests

from .utils import skipif_no_network
from ..datacite import _get_datacite_schema, to_datacite
from ..models import LicenseType, PublishedDandiset, RelationType, RoleType


def datacite_post(datacite, doi):
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


def _clean_doi(doi):
    """Remove doi. Status code is ignored"""
    requests.delete(
        f"https://api.test.datacite.org/dois/{doi}",
        auth=("DARTLIB.DANDI", os.environ["DATACITE_DEV_PASSWORD"]),
    )


@skipif_no_network
@pytest.fixture(scope="module")
def schema():
    return _get_datacite_schema()


@pytest.fixture(scope="function")
def metadata_basic():
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
                "roleName": [RoleType("dcite:ContactPerson")],
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


def _basic_publishmeta(dandi_id, version="0.0.0", prefix="10.80507"):
    """Return extra metadata required by PublishedDandiset

    Returned fields are additional to fields required by Dandiset
    """
    publish_meta = {
        "datePublished": str(datetime.now().year),
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
                    "version": "0.1.0",
                    "schemaKey": "Software",
                }
            ],
            "schemaKey": "PublishActivity",
        },
        "version": version,
        "doi": f"{prefix}/dandi.{dandi_id}/{version}",
    }
    return publish_meta


@skipif_no_network
@pytest.mark.skipif(
    not os.getenv("DATACITE_DEV_PASSWORD"), reason="no datacite password available"
)
@pytest.mark.parametrize("dandi_id", ["000004", "000008"])
def test_datacite(dandi_id, schema):
    """ checking to_datacite for a specific datasets"""

    # reading metadata taken from exemplary dandisets and saved in json files
    with (
        Path(__file__).with_name("data") / "metadata" / f"meta_{dandi_id}.json"
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
                "publisher": (None, "DANDI Archive"),
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
                    },
                    {
                        "name": "B_last, B_first",
                        "roleName": [RoleType("dcite:Author")],
                    },
                    {"name": "C_last, C_first"},
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
                    },
                    {
                        "name": "B_last, B_first",
                        "roleName": [RoleType("dcite:Sponsor")],
                    },
                ],
            },
            {
                "creators": (1, {"name": "A_last, A_first"}),
                "fundingReferences": (1, {"funderName": "B_last, B_first"}),
            },
        ),
        # additional contributor with 2 roles: Author and Software (doesn't exist in datacite)
        # the person should be in creators and contributors (with contributorType Other)
        # Adding Orcid ID to one of the contributors
        (
            {
                "contributor": [
                    {
                        "name": "A_last, A_first",
                        "roleName": [
                            RoleType("dcite:Author"),
                            RoleType("dcite:Software"),
                        ],
                        "orcidID": "orcid.org/0000-0001-0000-0000"
                    },
                    {
                        "name": "B_last, B_first",
                        "roleName": [RoleType("dcite:ContactPerson")],
                    },
                ],
            },
            {
                "creators": (1, {"name": "A_last, A_first",
                                 'nameIdentifiers': [{
                                     "nameIdentifier": "orcid.org/0000-0001-0000-0000",
                                     "nameIdentifierScheme": "ORCID",
                                     "schemeUri": "https://orcid.org/",
                                 }],
                                 }),
                "contributors": (
                    2,
                    {"name": "A_last, A_first", "contributorType": "Other",
                     'nameIdentifiers': [{
                         "nameIdentifier": "orcid.org/0000-0001-0000-0000",
                         "nameIdentifierScheme": "ORCID",
                         "schemeUri": "https://orcid.org/",
                     }],
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
def test_dandimeta_datacite(schema, metadata_basic, additional_meta, datacite_checks):
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

    # trying to poste datacite
    datacite_post(datacite, metadata_basic["doi"])


def test_datacite_publish(metadata_basic):

    dandi_id = metadata_basic["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    version = metadata_basic["version"]
    metadata_basic.update(_basic_publishmeta(dandi_id=dandi_id_noprefix))

    # creating and validating datacite objects
    datacite = to_datacite(metadata_basic, publish=True)

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
                        "schemeURI": "orcid.org",
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
                        "schemeURI": "orcid.org",
                    }
                ],
                "descriptions": [
                    {"description": "testing", "descriptionType": "Abstract"}
                ],
                "doi": f"10.80507/dandi.{dandi_id_noprefix}/{version}",
                "identifiers": [
                    {
                        "identifier": (
                            f"https://doi.org/10.80507"
                            f"/dandi.{dandi_id_noprefix}/{version}"
                        ),
                        "identifierType": "DOI",
                    },
                    {
                        "identifier": f"https://identifiers.org/{dandi_id}/{version}",
                        "identifierType": "URL",
                    },
                    {
                        "identifier": (
                            f"https://dandiarchive.org/dandiset"
                            f"/{dandi_id_noprefix}/{version}"
                        ),
                        "identifierType": "URL",
                    },
                ],
                "publicationYear": "1970",
                "publisher": "DANDI Archive",
                "rightsList": [
                    {
                        "rightsIdentifier": "CC_BY_40",
                        "rightsIdentifierScheme": "SPDX",
                        "schemeURI": "https://spdx.org/licenses/",
                    }
                ],
                "schemaVersion": "http://datacite.org/schema/kernel-4",
                "titles": [{"title": "testing dataset"}],
                "types": {
                    "resourceType": "Neural Data",
                    "resourceTypeGeneral": "Dataset",
                },
                "url": f"https://dandiarchive.org/dandiset/{dandi_id_noprefix}/{version}",
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
def test_datacite_related_res_url(metadata_basic, related_res_url, related_ident_exp):
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
