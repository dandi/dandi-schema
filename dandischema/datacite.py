from copy import deepcopy

from .models import Organization, Person, PublishedDandisetMeta, RoleType

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
DATACITE_MAP = dict([(el.lower(), el) for el in DATACITE_IDENTYPE])


def to_datacite(meta):
    """Convert published Dandiset metadata to Datacite"""
    if not isinstance(meta, PublishedDandisetMeta):
        meta = PublishedDandisetMeta(**meta)

    attributes = {}
    attributes["identifiers"] = [
        # TODO: the first element is ignored, not sure how to fix it...
        {"identifier": f"https://doi.org/{meta.doi}", "identifierType": "DOI"},
        {
            "identifier": f"https://identifiers.org/{meta.id}",
            "identifierType": "URL",
        },
        {
            "identifier": f"https://dandiarchive.org/dandiset/{meta.identifier}",
            "identifierType": "URL",
        },
    ]

    attributes["doi"] = meta.doi
    attributes["titles"] = [{"title": meta.name}]
    attributes["descriptions"] = [
        {"description": meta.description, "descriptionType": "Abstract"}
    ]
    attributes["publisher"] = "DANDI Archive"
    attributes["publicationYear"] = str(meta.datePublished.year)
    # not sure about it dandi-api had "resourceTypeGeneral": "NWB"
    attributes["types"] = {"resourceType": "NWB", "resourceTypeGeneral": "Dataset"}
    # meta has also attribute url, but it often empty
    attributes["url"] = meta.url
    # assuming that all licenses are from SPDX?
    attributes["rightsList"] = [
        {
            "schemeURI": "https://spdx.org/licenses/",
            "rightsIdentifierScheme": "SPDX",
            "rightsIdentifier": el.name,
        }
        for el in meta.license
    ]
    attributes["schemaVersion"] = "http://datacite.org/schema/kernel-4"

    contributors = []
    creators = []
    for contr_el in meta.contributor:
        if RoleType("dandirole:Sponsor") in contr_el.roleName:
            # no info about "funderIdentifierType", "awardUri", "awardTitle"
            dict_fund = {"funderName": contr_el.name}
            if contr_el.identifier:
                dict_fund["funderIdentifier"] = contr_el.identifier
            if contr_el.awardNumber:
                dict_fund["awardNumber"] = contr_el.awardNumber
            attributes.setdefault("fundingReferences", []).append(dict_fund)
            # if no more roles, it shouldn't be added to creators or contributors
            contr_el.roleName.remove(RoleType("dandirole:Sponsor"))
            if not contr_el.roleName:
                continue

        contr_dict = {
            "name": contr_el.name,
            "contributorName": contr_el.name,
            "schemeURI": "orcid.org",
        }
        if isinstance(contr_el, Person):
            contr_dict["nameType"] = "Personal"
            if len(contr_el.name.split(",")) == 2:
                contr_dict["familyName"], contr_dict["givenName"] = contr_el.name.split(
                    ","
                )
            if getattr(contr_el, "affiliation"):
                contr_dict["affiliation"] = [
                    {"name": el.name} for el in contr_el.affiliation
                ]
            else:
                contr_dict["affiliation"] = []
        elif isinstance(contr_el, Organization):
            contr_dict["nameType"] = "Organizational"

        if RoleType("dandirole:Author") in getattr(contr_el, "roleName"):
            create_dict = deepcopy(contr_dict)
            create_dict["creatorName"] = create_dict.pop("contributorName")
            creators.append(create_dict)
            contr_el.roleName.remove(RoleType("dandirole:Author"))
            # if no more roles, it shouldn't be added to contributors
            if not contr_el.roleName:
                continue

        if getattr(contr_el, "roleName"):
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

    if getattr(meta, "relatedResource"):
        attributes["relatedIdentifiers"] = []
        for rel_el in meta.relatedResource:
            ident = rel_el.identifier.split(":")
            if len(ident) == 2:
                ident_tp, ident_nr = ident
                if ident_tp.lower() in DATACITE_MAP:
                    ident_tp = DATACITE_MAP[ident_tp.lower()]
                else:
                    raise ValueError(
                        f"identifier has to be from the list: {DATACITE_IDENTYPE}, "
                        f"but {ident_tp} provided"
                    )
            else:
                raise ValueError(
                    "identifier is expected to be type:number,"
                    f" got {rel_el.identifier}"
                )
            rel_dict = {
                "relatedIdentifier": ident_nr,
                # in theory it should be from the specific list that contains e.g. DOI, arXiv, ...
                "relatedIdentifierType": ident_tp,
                "relationType": rel_el.relation.name,
            }
            attributes["relatedIdentifiers"].append(rel_dict)

    if getattr(meta, "keywords"):
        attributes["subjects"] = [{"subject": el} for el in meta.keywords]

    datacite_dict = {"data": {"id": meta.doi, "type": "dois", "attributes": attributes}}
    return datacite_dict
