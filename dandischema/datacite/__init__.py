"""
Interfaces and data to interact with DataCite metadata
"""

# TODO: RF into submodules for some next "minor" taking care not to break

from copy import deepcopy
from functools import lru_cache
import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, Optional, Tuple, Union
from warnings import warn

from jsonschema import Draft7Validator
from pydantic import ValidationError
import requests

from ..models import (
    LicenseType,
    NAME_PATTERN,
    Dandiset,
    Organization,
    Person,
    PublishedDandiset,
    RelationType,
    Resource,
    RoleType,
)

logger = logging.getLogger(__name__)

DATACITE_CONTRTYPE = {
    "ContactPerson",
    "DataCollector",
    "DataCurator",
    "DataManager",
    "Distributor",
    "Editor",
    "HostingInstitution",
    "Producer",
    "ProjectLeader",
    "ProjectManager",
    "ProjectMember",
    "RegistrationAgency",
    "RegistrationAuthority",
    "RelatedPerson",
    "Researcher",
    "ResearchGroup",
    "RightsHolder",
    "Sponsor",
    "Supervisor",
    "WorkPackageLeader",
    "Other",
}


DATACITE_IDENTYPE = {
    "ARK",
    "arXiv",
    "bibcode",
    "DOI",
    "EAN13",
    "EISSN",
    "Handle",
    "IGSN",
    "ISBN",
    "ISSN",
    "ISTC",
    "LISSN",
    "LSID",
    "PMID",
    "PURL",
    "UPC",
    "URL",
    "URN",
    "w3id",
}
DATACITE_MAP = {el.lower(): el for el in DATACITE_IDENTYPE}


def construct_unvalidated_dandiset(meta_dict: dict) -> Dandiset:
    """
    Construct a Dandiset model from a dictionary without validation.
    """
    meta = Dandiset.model_construct(**meta_dict)

    # model_construct doesn't handle nested objects so we have to init classes manually
    if hasattr(meta, 'license') and meta.license:
        processed_licenses = []
        for license_item in meta.license:
            processed_licenses.append(LicenseType(license_item))
        meta.license = processed_licenses

    if hasattr(meta, 'contributor') and meta.contributor:
        for i, contributor_dict in enumerate(meta.contributor):
            if 'roleName' in contributor_dict and contributor_dict['roleName']:
                processed_roles = []
                for role in contributor_dict['roleName']:
                    processed_roles.append(RoleType(role))
                contributor_dict['roleName'] = processed_roles

            # Based on schemaKey, convert to proper model type
            schema_key = contributor_dict.get('schemaKey')
            if schema_key == 'Person':
                meta.contributor[i] = Person.model_construct(**contributor_dict)
            elif schema_key == 'Organization':
                meta.contributor[i] = Organization.model_construct(**contributor_dict)

    if hasattr(meta, 'relatedResource') and meta.relatedResource:
        for i, resource_dict in enumerate(meta.relatedResource):
            if 'relation' in resource_dict:
                resource_dict['relation'] = RelationType(resource_dict['relation'])
            meta.relatedResource[i] = Resource.model_construct(**resource_dict)

    return meta


def to_datacite(
    meta: Union[dict, PublishedDandiset],
    validate: bool = False,
    publish: bool = False,
    *,
    event: Optional[str] = None,
) -> dict:
    """
    Convert Dandiset metadata to DataCite payload.

    This function tries to validate the metadata against PublishedDandiset model.
    If strict validation fails, it falls back to using construct_unvalidated_dandiset()
    to build the model without validation but with properly handled nested types.
    """
    # Try to convert dict to model if needed
    if isinstance(meta, dict):
        meta = deepcopy(meta)
        try:
            # First try PublishedDandiset
            meta = PublishedDandiset(**meta)
        except ValidationError:
            # If that fails, use construct_unvalidated_dandiset
            logger.exception("Validation failed, using construct_unvalidated_dandiset()")
            meta = construct_unvalidated_dandiset(meta)

    attributes: Dict[str, Any] = {}

    if event is not None and publish:
        raise ValueError(
            "Cannot use both 'event' and deprecated 'publish'. Use only 'event'."
        )

    # If there is no attributes["event"] a Draft DOI is minted
    if event is not None:
        if event not in {"publish", "hide"}:
            raise ValueError("Invalid event value: must be 'publish' or 'hide'")
        attributes["event"] = event
    elif publish:
        warn(
            "'publish' is deprecated; use 'event=\"publish\"' instead",
            DeprecationWarning,
            stacklevel=2,
        )
        attributes["event"] = "publish"

    attributes["alternateIdentifiers"] = [
        {
            "alternateIdentifier": f"https://identifiers.org/{meta.id}",
            "alternateIdentifierType": "URL",
        },
        {
            "alternateIdentifier": str(meta.url),
            "alternateIdentifierType": "URL",
        },
    ]

    attributes["doi"] = meta.doi
    if meta.version:
        attributes["version"] = meta.version
    attributes["titles"] = [{"title": meta.name}]
    attributes["descriptions"] = [
        {"description": meta.description, "descriptionType": "Abstract"}
    ]
    attributes["publisher"] = {
        "name": "DANDI Archive",
        "schemeUri": "https://scicrunch.org/resolver/",
        "publisherIdentifier": "https://scicrunch.org/resolver/RRID:SCR_017571",
        "publisherIdentifierScheme": "RRID",
        "lang": "en",
    }

    # Only include publicationYear if datePublished is available (for published Dandisets)
    if hasattr(meta, "datePublished") and meta.datePublished:
        attributes["publicationYear"] = str(meta.datePublished.year)

    # not sure about it dandi-api had "resourceTypeGeneral": "NWB"
    attributes["types"] = {
        "resourceType": "Neural Data",
        "resourceTypeGeneral": "Dataset",
    }
    # meta has also attribute url, but it often empty
    attributes["url"] = str(meta.url or "")
    # assuming that all licenses are from SPDX?
    attributes["rightsList"] = [
        {
            "schemeUri": "https://spdx.org/licenses/",
            "rightsIdentifierScheme": "SPDX",
            "rightsIdentifier": el.name,
        }
        for el in meta.license
    ]
    attributes["schemaVersion"] = "http://datacite.org/schema/kernel-4"

    contributors = []
    creators = []
    for contr_el in meta.contributor:
        if contr_el.roleName and (
            RoleType("dcite:Sponsor") in contr_el.roleName
            or RoleType("dcite:Funder") in contr_el.roleName
        ):
            # no info about "funderIdentifierType", "awardUri", "awardTitle"
            dict_fund = {"funderName": contr_el.name}
            if contr_el.identifier:
                dict_fund["funderIdentifier"] = contr_el.identifier
                funderidtype = "Other"
                if "ror.org" in contr_el.identifier:
                    funderidtype = "ROR"
                dict_fund["funderIdentifierType"] = funderidtype
            if contr_el.awardNumber:
                dict_fund["awardNumber"] = contr_el.awardNumber
            attributes.setdefault("fundingReferences", []).append(dict_fund)
            # if no more roles, it shouldn't be added to creators or contributors
            if RoleType("dcite:Sponsor") in contr_el.roleName:
                contr_el.roleName.remove(RoleType("dcite:Sponsor"))
            if RoleType("dcite:Funder") in contr_el.roleName:
                contr_el.roleName.remove(RoleType("dcite:Funder"))
            if not contr_el.roleName:
                continue

        contr_dict: Dict[str, Any] = {
            "name": contr_el.name,
            "contributorName": contr_el.name,
            "schemeUri": "orcid.org",
        }
        if isinstance(contr_el, Person):
            contr_dict["nameType"] = "Personal"
            contr_dict["familyName"], contr_dict["givenName"] = re.findall(
                NAME_PATTERN, contr_el.name
            ).pop()

            if hasattr(contr_el, "affiliation") and contr_el.affiliation is not None:
                contr_dict["affiliation"] = [
                    {"name": el.name} for el in contr_el.affiliation
                ]
            else:
                contr_dict["affiliation"] = []
            if getattr(contr_el, "identifier"):
                orcid_dict = {
                    "nameIdentifier": f"https://orcid.org/{contr_el.identifier}",
                    "nameIdentifierScheme": "ORCID",
                    "schemeUri": "https://orcid.org/",
                }
                contr_dict["nameIdentifiers"] = [orcid_dict]

        elif isinstance(contr_el, Organization):
            contr_dict["nameType"] = "Organizational"

        if contr_el.roleName and RoleType("dcite:Author") in contr_el.roleName:
            create_dict = deepcopy(contr_dict)
            create_dict["creatorName"] = create_dict.pop("contributorName")
            creators.append(create_dict)
            contr_el.roleName.remove(RoleType("dcite:Author"))
            # if no more roles, it shouldn't be added to contributors
            if not contr_el.roleName:
                continue

        contr_all = []
        if contr_el.roleName:
            contr_all = [
                el.name for el in contr_el.roleName if el.name in DATACITE_CONTRTYPE
            ]
        if contr_all:
            contr_dict["contributorType"] = contr_all[0]
        else:
            contr_dict["contributorType"] = "Other"
        contributors.append(contr_dict)

    # if there are no creators, the first contributor is also treated as the creator
    if not creators and contributors:
        creators = [deepcopy(contributors[0])]
        creators[0]["creatorName"] = creators[0].pop("contributorName")
        creators[0].pop("contributorType")

    attributes["contributors"] = contributors
    attributes["creators"] = creators

    if hasattr(meta, "relatedResource") and meta.relatedResource:
        attributes["relatedIdentifiers"] = []
        for rel_el in meta.relatedResource:
            if rel_el.identifier is not None:
                if rel_el.identifier.lower().startswith("doi:"):
                    ident_tp, ident_id = rel_el.identifier.split(":", 1)
                    if ident_tp.lower() in DATACITE_MAP:
                        ident_tp = DATACITE_MAP[ident_tp.lower()]
                    else:
                        raise ValueError(
                            f"identifier has to be from the list: {DATACITE_IDENTYPE}, "
                            f"but {ident_tp} provided"
                        )
                else:  # trying to find identifier if url provided
                    if "doi.org/" in rel_el.identifier:
                        ident_tp = "DOI"
                        ident_id = rel_el.identifier.split("doi.org/")[1]
                    elif "biorxiv.org/" in rel_el.identifier:
                        ident_tp = "DOI"
                        ident_id = rel_el.identifier.split("biorxiv.org/content/")[
                            1
                        ].split("v")[0]
                    # if any other url is passed
                    elif rel_el.identifier.startswith("https://"):
                        ident_id = rel_el.identifier
                        ident_tp = "URL"
                    else:
                        continue
            elif rel_el.url is not None:
                ident_id = str(rel_el.url)
                ident_tp = "URL"
            rel_dict = {
                "relatedIdentifier": ident_id.lower(),
                # in theory it should be from the specific list that contains e.g. DOI, arXiv, ...
                "relatedIdentifierType": ident_tp.upper(),
                "relationType": rel_el.relation.name,
            }
            attributes["relatedIdentifiers"].append(rel_dict)

    if hasattr(meta, "keywords") and meta.keywords is not None:
        attributes["subjects"] = [{"subject": el} for el in meta.keywords]

    datacite_dict = {"data": {"id": meta.doi, "type": "dois", "attributes": attributes}}

    if validate:
        validate_datacite(datacite_dict)

    return datacite_dict


@lru_cache()
def _get_datacite_schema(version_id: str = "inveniosoftware-4.5-81-g160250d") -> Any:
    """Load datacite schema based on the version id provided."""
    schema_folder = Path(__file__).parent / "schema"
    return json.loads((schema_folder / f"{version_id}.json").read_text())


def validate_datacite(datacite_dict: dict) -> None:
    schema = _get_datacite_schema()
    Draft7Validator.check_schema(schema)
    validator = Draft7Validator(schema)
    validator.validate(datacite_dict["data"]["attributes"])
