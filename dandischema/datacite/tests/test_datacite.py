from enum import Enum
import json
import os
import random
from time import sleep
from typing import TYPE_CHECKING, Any, Dict, Tuple, cast

from jsonschema import Draft7Validator
import pytest
import requests

from dandischema.conf import get_instance_config
from dandischema.models import (
    LicenseType,
    PublishedDandiset,
    RelationType,
    ResourceType,
    RoleType,
)
from dandischema.tests.utils import (
    DANDISET_METADATA_DIR,
    DOI_PREFIX,
    INSTANCE_NAME,
    basic_publishmeta,
    skipif_no_datacite_auth,
    skipif_no_doi_prefix,
    skipif_no_network,
    skipif_no_test_dandiset_metadata_dir,
)

from .. import _get_datacite_schema, _licenses_to_rights_list, to_datacite

_INSTANCE_CONFIG = get_instance_config()


class TestLicensesToRightsList:
    """
    Tests for the `_licenses_to_rights_list()` helper function.
    """

    @pytest.mark.parametrize(
        "licenses",
        [
            [" "],
            ["bad_license"],
            [" spdx:CC0-1.0"],
            ["spdx:CC0-1.0 "],
            ["spdx: CC0-1.0"],
            ["spdx:CC0-1.0", "foo-license"],
        ],
    )
    def test_bad_format(self, licenses: list[str]) -> None:
        """
        Test handling of licenses with a value of  bad format
        """
        if TYPE_CHECKING:

            # noinspection PyUnusedLocal
            class BadLicenseType(Enum):
                ...  # fmt: skip

        else:
            # noinspection PyPep8Naming
            BadLicenseType = Enum(
                "BadLicenseType",
                [(f"M{idx}", license_) for idx, license_ in enumerate(licenses)],
            )

            with pytest.raises(AssertionError, match="not of the expected format"):
                _licenses_to_rights_list(list(BadLicenseType))

    @pytest.mark.parametrize(
        "licenses",
        [
            ["foo:license"],
            ["bar:license"],
            ["foo:license", "bar:license"],
        ],
    )
    def test_non_spdx_license(self, licenses: list[str]) -> None:
        """
        Test handling of licenses not denoted using the `"spdx"` schema, i.e.
        licenses that are not in the SPDX license list at
        https://spdx.org/licenses/
        """
        if TYPE_CHECKING:
            # noinspection PyUnusedLocal
            class NonSpdxLicenseType(Enum):
                ...  # fmt: skip

        else:
            # noinspection PyPep8Naming
            NonSpdxLicenseType = Enum(
                "NonSpdxLicenseType",
                [(f"M{idx}", license_) for idx, license_ in enumerate(licenses)],
            )

        with pytest.raises(
            NotImplementedError, match="Currently only SPDX licenses are supported"
        ):
            _licenses_to_rights_list(list(NonSpdxLicenseType))

    @pytest.mark.parametrize(
        "licenses",
        [
            ["spdx:CC0-1.0"],
            ["spdx:CC-BY-4.0"],
            ["spdx:CC0-1.0", "spdx:CC-BY-4.0"],
        ],
    )
    def test_valid_input(self, licenses: list[str]) -> None:
        """
        Test handling of valid input
        """
        if TYPE_CHECKING:
            # noinspection PyUnusedLocal
            class ValidLicenseType(Enum):
                ...  # fmt: skip

        else:
            # noinspection PyPep8Naming
            ValidLicenseType = Enum(
                "ValidLicenseType",
                [(license_,) * 2 for license_ in licenses],
            )

        expected_rights_list = [
            {
                "rightsIdentifier": license_.removeprefix("spdx:"),
                "rightsIdentifierScheme": "SPDX",
                "schemeUri": "https://spdx.org/licenses/",
            }
            for license_ in licenses
        ]

        assert (
            _licenses_to_rights_list(
                cast(
                    list[LicenseType],
                    [ValidLicenseType(license_) for license_ in licenses],
                )
            )
            == expected_rights_list
        )


def datacite_post(datacite: dict, doi: str) -> None:
    """Post the datacite object and check the status of the request"""

    # removing doi in case it exists
    _clean_doi(doi)

    # checking f I'm able to create doi
    rp = requests.post(
        "https://api.test.datacite.org/dois",
        json=datacite,
        headers={"Content-Type": "application/vnd.api+json"},
        auth=(os.environ["DATACITE_DEV_LOGIN"], os.environ["DATACITE_DEV_PASSWORD"]),
    )
    rp.raise_for_status()

    # Wait for DataCite to correctly process the DOI creation
    #   to avoid the bug documented in https://github.com/datacite/datacite/issues/2307
    sleep(3)

    # checking if i'm able to get the url
    rg = requests.get(url=f"https://api.test.datacite.org/dois/{doi}/activities")
    rg.raise_for_status()

    # cleaning url
    _clean_doi(doi)


def _clean_doi(doi: str) -> None:
    """Remove doi. Status code is ignored"""
    requests.delete(
        f"https://api.test.datacite.org/dois/{doi}",
        auth=(os.environ["DATACITE_DEV_LOGIN"], os.environ["DATACITE_DEV_PASSWORD"]),
    )


@pytest.fixture(scope="module")
def schema() -> Any:
    return _get_datacite_schema()


@pytest.fixture(scope="function")
def metadata_basic() -> Dict[str, Any]:
    dandi_id_noprefix = f"000{random.randrange(100, 999)}"
    dandi_id = f"{INSTANCE_NAME}:{dandi_id_noprefix}"
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
@skipif_no_datacite_auth
@skipif_no_doi_prefix
@skipif_no_test_dandiset_metadata_dir
@pytest.mark.parametrize("dandi_id", ["000004", "000008"])
def test_datacite(dandi_id: str, schema: Any) -> None:
    """checking to_datacite for a specific datasets"""

    assert DOI_PREFIX is not None

    # reading metadata taken from exemplary dandisets and saved in json files
    with (DANDISET_METADATA_DIR / f"meta_{dandi_id}.json").open() as f:
        meta_js = json.load(f)

    version = "0.0.0"
    meta_js["id"] = meta_js["id"].replace(meta_js["version"], version)
    meta_js["url"] = meta_js["url"].replace(meta_js["version"], version)
    meta_js["version"] = version

    # updating with basic fields required for PublishDandiset
    meta_js.update(
        basic_publishmeta(
            INSTANCE_NAME,
            dandi_id.replace("000", str(random.randrange(100, 999))),
            prefix=DOI_PREFIX,
        )
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
                        "name": f"{_INSTANCE_CONFIG.instance_name} Archive",
                        "publisherIdentifier": f"https://scicrunch.org/resolver/"
                        f"{_INSTANCE_CONFIG.instance_identifier}",
                        "publisherIdentifierScheme": "RRID",
                        "schemeUri": "https://scicrunch.org/resolver/",
                        "lang": "en",
                    },
                ),
                "rightsList": (
                    1,
                    {"rightsIdentifierScheme": "SPDX", "rightsIdentifier": "CC-BY-4.0"},
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
@skipif_no_datacite_auth
@skipif_no_doi_prefix
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

    assert DOI_PREFIX is not None

    dandi_id = metadata_basic["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]

    metadata_basic.update(
        basic_publishmeta(INSTANCE_NAME, dandi_id=dandi_id_noprefix, prefix=DOI_PREFIX)
    )
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


@skipif_no_doi_prefix
def test_datacite_publish(metadata_basic: Dict[str, Any]) -> None:
    assert DOI_PREFIX is not None

    dandi_id = metadata_basic["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]
    version = metadata_basic["version"]
    metadata_basic.update(
        basic_publishmeta(INSTANCE_NAME, dandi_id=dandi_id_noprefix, prefix=DOI_PREFIX)
    )

    # creating and validating datacite objects
    datacite = to_datacite(metadata_basic, publish=True, validate=True)

    assert datacite == {
        # 'data': {}
        "data": {
            "id": f"{DOI_PREFIX}/{INSTANCE_NAME.lower()}.{dandi_id_noprefix}/{version}",
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
                "doi": (
                    f"{DOI_PREFIX}/"
                    f"{INSTANCE_NAME.lower()}.{dandi_id_noprefix}/{version}"
                ),
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
                    "name": f"{_INSTANCE_CONFIG.instance_name} Archive",
                    "publisherIdentifier": f"https://scicrunch.org/resolver/"
                    f"{_INSTANCE_CONFIG.instance_identifier}",
                    "publisherIdentifierScheme": "RRID",
                    "schemeUri": "https://scicrunch.org/resolver/",
                    "lang": "en",
                },
                "rightsList": [
                    {
                        "rightsIdentifier": "CC-BY-4.0",
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
@skipif_no_doi_prefix
def test_datacite_related_res_url(
    metadata_basic: Dict[str, Any],
    related_res_url: Dict[str, Any],
    related_ident_exp: Tuple[str, str],
) -> None:
    """
    checking if urls provided in the relatedResource.identifier could be
    translated to DOI for some websites: e.g. bioarxiv.org, doi.org
    """
    assert DOI_PREFIX is not None

    dandi_id = metadata_basic["identifier"]
    dandi_id_noprefix = dandi_id.split(":")[1]

    metadata_basic.update(
        basic_publishmeta(INSTANCE_NAME, dandi_id=dandi_id_noprefix, prefix=DOI_PREFIX)
    )
    metadata_basic["relatedResource"] = [related_res_url]

    # creating and validating datacite objects
    datacite = to_datacite(metadata_basic)
    relIdent = datacite["data"]["attributes"]["relatedIdentifiers"][0]
    assert relIdent["relatedIdentifier"] == related_ident_exp[0].lower()
    assert relIdent["relatedIdentifierType"] == related_ident_exp[1]
