from datetime import datetime
import json
import os
from pathlib import Path
import random

from jsonschema import Draft6Validator
import pytest
import requests

from ..datacite import to_datacite
from ..models import LicenseType, PublishedDandisetMeta, RoleType


def datacite_post(datacite, doi):
    """ posting the datacite object and checking the status of the requests"""

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
    """removing doi, ignoring the status code"""
    requests.delete(
        f"https://api.test.datacite.org/dois/{doi}",
        auth=("DARTLIB.DANDI", os.environ["DATACITE_DEV_PASSWORD"]),
    )


@pytest.fixture(scope="module")
def schema():
    sr = requests.get(
        "https://raw.githubusercontent.com/datacite/schema/master/source/"
        "json/kernel-4.3/datacite_4.3_schema.json"
    )
    sr.raise_for_status()
    schema = sr.json()
    return schema


def _basic_publishmeta(dandi_id, version="v.0", prefix="10.80507"):
    """
    adding basic info required by PublishedDandisetMeta in addition to
    fields required by DandisetMeta
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
                    "id": "RRID:SCR_017571",
                    "name": "DANDI API",
                    "version": "0.1.0",
                    "schemaKey": "Software",
                }
            ],
            "schemaKey": "PublishActivity",
        },
        "version": version,
        "doi": f"{prefix}/dandi.{dandi_id}.{version}",
    }
    return publish_meta


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

    # updating with basic fields required for PublishDandisetMeta
    meta_js.update(
        _basic_publishmeta(dandi_id.replace("000", str(random.randrange(100, 999))))
    )
    meta = PublishedDandisetMeta(**meta_js)

    datacite = to_datacite(meta=meta)

    Draft6Validator.check_schema(schema)
    validator = Draft6Validator(schema)
    validator.validate(datacite["data"]["attributes"])

    # trying to post datacite
    datacite_post(datacite, meta.doi)


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
                    {"resourceType": "NWB", "resourceTypeGeneral": "Dataset"},
                ),
            },
        ),
        # additional contributor with dandi:Author
        (
            {
                "contributor": [
                    {
                        "name": "A_last, A_first",
                        "roleName": [RoleType("dandirole:ContactPerson")],
                    },
                    {
                        "name": "B_last, B_first",
                        "roleName": [RoleType("dandirole:Author")],
                    },
                ],
            },
            {
                "creators": (1, {"name": "B_last, B_first"}),
                "contributors": (
                    1,
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
                        "roleName": [RoleType("dandirole:ContactPerson")],
                    },
                    {
                        "name": "B_last, B_first",
                        "roleName": [RoleType("dandirole:Sponsor")],
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
        (
            {
                "contributor": [
                    {
                        "name": "A_last, A_first",
                        "roleName": [
                            RoleType("dandirole:Author"),
                            RoleType("dandirole:Software"),
                        ],
                    },
                    {
                        "name": "B_last, B_first",
                        "roleName": [RoleType("dandirole:ContactPerson")],
                    },
                ],
            },
            {
                "creators": (1, {"name": "A_last, A_first"}),
                "contributors": (
                    2,
                    {"name": "A_last, A_first", "contributorType": "Other"},
                ),
            },
        ),
    ],
)
@pytest.mark.skipif(
    not os.getenv("DATACITE_DEV_PASSWORD"), reason="no datacite password available"
)
def test_dantimeta_datacite(schema, additional_meta, datacite_checks):
    """
    checking datacite objects for specific metadata dictionaries,
    posting datacite object and checking the status code
    """

    dandi_id = f"DANDI:000{random.randrange(100, 999)}"

    # meta data without doi, datePublished and publishedBy
    meta_dict = {
        "identifier": dandi_id,
        "id": f"{dandi_id}/draft",
        "name": "testing dataset",
        "description": "testing",
        "contributor": [
            {
                "name": "A_last, A_first",
                "roleName": [RoleType("dandirole:ContactPerson")],
            }
        ],
        "license": [LicenseType("spdx:CC-BY-4.0")],
    }
    meta_dict.update(_basic_publishmeta(dandi_id=dandi_id))
    meta_dict.update(additional_meta)

    # creating and validating datacite objects
    datacite = to_datacite(meta_dict)
    Draft6Validator.check_schema(schema)
    validator = Draft6Validator(schema)
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
    datacite_post(datacite, meta_dict["doi"])