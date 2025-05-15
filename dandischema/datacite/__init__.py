"""
Interfaces and data to interact with DataCite metadata
"""

# TODO: RF into submodules for some next "minor" taking care not to break

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Any, Dict, Union

from jsonschema import Draft7Validator
import requests

from ..models import (
    NAME_PATTERN,
    Dandiset,
    Organization,
    Person,
    PublishedDandiset,
    RoleType,
)

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


def to_datacite(
    meta: Union[dict, PublishedDandiset],
    validate: bool = False,
    publish: bool = False,
) -> dict:
    """Convert published Dandiset metadata to Datacite"""

    # checking the version, create Dandiset for draft version and PublishedDandiset otherwise
    if isinstance(meta, dict):
        if meta.get("version") == "draft":
            meta = Dandiset(**meta)
        else:
            meta = PublishedDandiset(**meta)

    attributes: Dict[str, Any] = {}
    if publish:
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

    if hasattr(meta, "doi"):
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
    if hasattr(meta, "datePublished"):
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
