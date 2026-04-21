from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
import re
import sys
from typing import Any, ClassVar, Literal, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer,
)

metamodel_version = "1.7.0"
version = "0.7.0"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias=True,
        validate_by_name=True,
        validate_assignment=True,
        validate_default=True,
        extra="forbid",
        arbitrary_types_allowed=True,
        use_enum_values=True,
        strict=False,
    )


class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key: str):
        return getattr(self.root, key)

    def __getitem__(self, key: str):
        return self.root[key]

    def __setitem__(self, key: str, value):
        self.root[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.root


linkml_meta = LinkMLMeta(
    {
        "default_prefix": "dandi",
        "default_range": "string",
        "id": "https://schema.dandiarchive.org/s/dandi/v0.7",
        "imports": ["linkml:types"],
        "name": "dandi-schema",
        "prefixes": {
            "DANDI": {
                "prefix_prefix": "DANDI",
                "prefix_reference": "http://dandiarchive.org/dandiset/",
            },
            "ORCID": {
                "prefix_prefix": "ORCID",
                "prefix_reference": "https://orcid.org/",
            },
            "PATO": {
                "prefix_prefix": "PATO",
                "prefix_reference": "http://purl.obolibrary.org/obo/PATO_",
            },
            "ROR": {"prefix_prefix": "ROR", "prefix_reference": "https://ror.org/"},
            "RRID": {
                "prefix_prefix": "RRID",
                "prefix_reference": "https://scicrunch.org/resolver/RRID:",
            },
            "dandi": {
                "prefix_prefix": "dandi",
                "prefix_reference": "http://schema.dandiarchive.org/",
            },
            "dandiasset": {
                "prefix_prefix": "dandiasset",
                "prefix_reference": "http://dandiarchive.org/asset/",
            },
            "dcite": {
                "prefix_prefix": "dcite",
                "prefix_reference": "http://schema.dandiarchive.org/datacite/",
            },
            "dct": {
                "prefix_prefix": "dct",
                "prefix_reference": "http://purl.org/dc/terms/",
            },
            "linkml": {
                "prefix_prefix": "linkml",
                "prefix_reference": "https://w3id.org/linkml/",
            },
            "nidm": {
                "prefix_prefix": "nidm",
                "prefix_reference": "http://purl.org/nidash/nidm#",
            },
            "owl": {
                "prefix_prefix": "owl",
                "prefix_reference": "http://www.w3.org/2002/07/owl#",
            },
            "pav": {"prefix_prefix": "pav", "prefix_reference": "http://purl.org/pav/"},
            "prov": {
                "prefix_prefix": "prov",
                "prefix_reference": "http://www.w3.org/ns/prov#",
            },
            "rdf": {
                "prefix_prefix": "rdf",
                "prefix_reference": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            },
            "rdfa": {
                "prefix_prefix": "rdfa",
                "prefix_reference": "http://www.w3.org/ns/rdfa#",
            },
            "rdfs": {
                "prefix_prefix": "rdfs",
                "prefix_reference": "http://www.w3.org/2000/01/rdf-schema#",
            },
            "rs": {
                "prefix_prefix": "rs",
                "prefix_reference": "http://schema.repronim.org/",
            },
            "schema": {
                "prefix_prefix": "schema",
                "prefix_reference": "http://schema.org/",
            },
            "skos": {
                "prefix_prefix": "skos",
                "prefix_reference": "http://www.w3.org/2004/02/skos/core#",
            },
            "spdx": {
                "prefix_prefix": "spdx",
                "prefix_reference": "http://spdx.org/licenses/",
            },
            "uuid": {
                "prefix_prefix": "uuid",
                "prefix_reference": "http://uuid.repronim.org/",
            },
            "xsd": {
                "prefix_prefix": "xsd",
                "prefix_reference": "http://www.w3.org/2001/XMLSchema#",
            },
        },
        "source_file": "dandischema/models.yaml",
        "status": "eunal:concept-status/DRAFT",
    }
)


class AccessType(str, Enum):
    """
    An enumeration of access status options
    """

    OpenAccess = "dandi:OpenAccess"
    EmbargoedAccess = "dandi:EmbargoedAccess"


class AgeReferenceType(str, Enum):
    """
    An enumeration of age reference
    """

    BirthReference = "dandi:BirthReference"
    GestationalReference = "dandi:GestationalReference"


class DigestType(str, Enum):
    """
    An enumeration of checksum types
    """

    md5 = "dandi:md5"
    sha1 = "dandi:sha1"
    sha2_256 = "dandi:sha2-256"
    sha3_256 = "dandi:sha3-256"
    blake2b_256 = "dandi:blake2b-256"
    blake3 = "dandi:blake3"
    dandi_etag = "dandi:dandi-etag"
    dandi_zarr_checksum = "dandi:dandi-zarr-checksum"


class IdentifierType(str, Enum):
    """
    An enumeration of identifiers
    """

    doi = "dandi:doi"
    orcid = "dandi:orcid"
    ror = "dandi:ror"
    dandi = "dandi:dandi"
    rrid = "dandi:rrid"


class LicenseType(str, Enum):
    """
    An enumeration.
    """

    CC_BY_4FULL_STOP0 = "spdx:CC-BY-4.0"
    CC0_1FULL_STOP0 = "spdx:CC0-1.0"


class ParticipantRelationType(str, Enum):
    """
    An enumeration of participant relations
    """

    isChildOf = "dandi:isChildOf"
    isParentOf = "dandi:isParentOf"
    isSiblingOf = "dandi:isSiblingOf"
    isMonozygoticTwinOf = "dandi:isMonozygoticTwinOf"
    isDizygoticTwinOf = "dandi:isDizygoticTwinOf"


class RelationType(str, Enum):
    """
    An enumeration of resource relations
    """

    IsCitedBy = "dcite:IsCitedBy"
    Cites = "dcite:Cites"
    IsSupplementTo = "dcite:IsSupplementTo"
    IsSupplementedBy = "dcite:IsSupplementedBy"
    IsContinuedBy = "dcite:IsContinuedBy"
    Continues = "dcite:Continues"
    Describes = "dcite:Describes"
    IsDescribedBy = "dcite:IsDescribedBy"
    HasMetadata = "dcite:HasMetadata"
    IsMetadataFor = "dcite:IsMetadataFor"
    HasVersion = "dcite:HasVersion"
    IsVersionOf = "dcite:IsVersionOf"
    IsNewVersionOf = "dcite:IsNewVersionOf"
    IsPreviousVersionOf = "dcite:IsPreviousVersionOf"
    IsPartOf = "dcite:IsPartOf"
    HasPart = "dcite:HasPart"
    IsReferencedBy = "dcite:IsReferencedBy"
    References = "dcite:References"
    IsDocumentedBy = "dcite:IsDocumentedBy"
    Documents = "dcite:Documents"
    IsCompiledBy = "dcite:IsCompiledBy"
    Compiles = "dcite:Compiles"
    IsVariantFormOf = "dcite:IsVariantFormOf"
    IsOriginalFormOf = "dcite:IsOriginalFormOf"
    IsIdenticalTo = "dcite:IsIdenticalTo"
    IsReviewedBy = "dcite:IsReviewedBy"
    Reviews = "dcite:Reviews"
    IsDerivedFrom = "dcite:IsDerivedFrom"
    IsSourceOf = "dcite:IsSourceOf"
    IsRequiredBy = "dcite:IsRequiredBy"
    Requires = "dcite:Requires"
    Obsoletes = "dcite:Obsoletes"
    IsObsoletedBy = "dcite:IsObsoletedBy"
    IsPublishedIn = "dcite:IsPublishedIn"


class ResourceType(str, Enum):
    """
    An enumeration of resource types
    """

    Audiovisual = "dcite:Audiovisual"
    Book = "dcite:Book"
    BookChapter = "dcite:BookChapter"
    Collection = "dcite:Collection"
    ComputationalNotebook = "dcite:ComputationalNotebook"
    ConferencePaper = "dcite:ConferencePaper"
    ConferenceProceeding = "dcite:ConferenceProceeding"
    DataPaper = "dcite:DataPaper"
    Dataset = "dcite:Dataset"
    Dissertation = "dcite:Dissertation"
    Event = "dcite:Event"
    Image = "dcite:Image"
    Instrument = "dcite:Instrument"
    InteractiveResource = "dcite:InteractiveResource"
    Journal = "dcite:Journal"
    JournalArticle = "dcite:JournalArticle"
    Model = "dcite:Model"
    OutputManagementPlan = "dcite:OutputManagementPlan"
    PeerReview = "dcite:PeerReview"
    PhysicalObject = "dcite:PhysicalObject"
    Preprint = "dcite:Preprint"
    Report = "dcite:Report"
    Service = "dcite:Service"
    Software = "dcite:Software"
    Sound = "dcite:Sound"
    Standard = "dcite:Standard"
    StudyRegistration = "dcite:StudyRegistration"
    Text = "dcite:Text"
    Workflow = "dcite:Workflow"
    Other = "dcite:Other"


class RoleType(str, Enum):
    """
    An enumeration of roles
    """

    Author = "dcite:Author"
    Conceptualization = "dcite:Conceptualization"
    ContactPerson = "dcite:ContactPerson"
    DataCollector = "dcite:DataCollector"
    DataCurator = "dcite:DataCurator"
    DataManager = "dcite:DataManager"
    FormalAnalysis = "dcite:FormalAnalysis"
    FundingAcquisition = "dcite:FundingAcquisition"
    Investigation = "dcite:Investigation"
    Maintainer = "dcite:Maintainer"
    Methodology = "dcite:Methodology"
    Producer = "dcite:Producer"
    ProjectLeader = "dcite:ProjectLeader"
    ProjectManager = "dcite:ProjectManager"
    ProjectMember = "dcite:ProjectMember"
    ProjectAdministration = "dcite:ProjectAdministration"
    Researcher = "dcite:Researcher"
    Resources = "dcite:Resources"
    Software = "dcite:Software"
    Supervision = "dcite:Supervision"
    Validation = "dcite:Validation"
    Visualization = "dcite:Visualization"
    Funder = "dcite:Funder"
    Sponsor = "dcite:Sponsor"
    StudyParticipant = "dcite:StudyParticipant"
    Affiliation = "dcite:Affiliation"
    EthicsApproval = "dcite:EthicsApproval"
    Other = "dcite:Other"


class DandiBaseModel(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "id": {
                    "description": "Uniform resource identifier",
                    "name": "id",
                    "required": False,
                }
            },
        }
    )

    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["DandiBaseModel"] = Field(
        default="DandiBaseModel",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class AccessRequirements(DandiBaseModel):
    """
    Information about access options for the dataset
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "contactPoint": {
                    "description": "Who or where to look for "
                    "information about access.",
                    "name": "contactPoint",
                },
                "description": {
                    "description": "Information about access "
                    "requirements when embargoed or "
                    "restricted",
                    "name": "description",
                    "required": False,
                },
            },
        }
    )

    contactPoint: Optional[ContactPoint] = Field(
        default=None,
        description="""Who or where to look for information about access.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["AccessRequirements", "EthicsApproval", "Organization"]
            }
        },
    )
    description: Optional[str] = Field(
        default=None,
        description="""Information about access requirements when embargoed or restricted""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "AccessRequirements",
                    "Activity",
                    "CommonModel",
                    "Equipment",
                ]
            }
        },
    )
    embargoedUntil: Optional[date] = Field(
        default=None,
        title="Embargo end date",
        description="""Date on which embargo ends.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["AccessRequirements"]}},
    )
    status: AccessType = Field(
        default=...,
        title="Access status",
        description="""The access status of the item.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["AccessRequirements"]}},
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["AccessRequirements"] = Field(
        default="AccessRequirements",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class Activity(DandiBaseModel):
    """
    Information about the Project activity
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "description": {
                    "description": "The description of the " "activity.",
                    "name": "description",
                    "required": False,
                },
                "identifier": {
                    "name": "identifier",
                    "range": "string",
                    "required": False,
                },
                "name": {
                    "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                    "description": "The name of the activity.",
                    "name": "name",
                    "required": True,
                    "title": "Title",
                },
            },
        }
    )

    description: Optional[str] = Field(
        default=None,
        description="""The description of the activity.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "AccessRequirements",
                    "Activity",
                    "CommonModel",
                    "Equipment",
                ]
            }
        },
    )
    endDate: Optional[datetime] = Field(
        default=None, json_schema_extra={"linkml_meta": {"domain_of": ["Activity"]}}
    )
    identifier: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    name: str = Field(
        default=...,
        title="Title",
        description="""The name of the activity.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    startDate: Optional[datetime] = Field(
        default=None, json_schema_extra={"linkml_meta": {"domain_of": ["Activity"]}}
    )
    used: Optional[list[Equipment]] = Field(
        default=None,
        description="""A listing of equipment used for the activity.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Activity"]}},
    )
    wasAssociatedWith: Optional[list[Union[Agent, Organization, Person, Software]]] = (
        Field(
            default=None,
            json_schema_extra={
                "linkml_meta": {
                    "any_of": [
                        {
                            "notes": [
                                "pydantic2linkml: Unable to translate the logic "
                                "contained in the after validation function, <function "
                                "Contributor.ensure_contact_person_has_email at "
                                "0xADDRESS>."
                            ],
                            "range": "Person",
                        },
                        {
                            "notes": [
                                "pydantic2linkml: Unable to translate the logic "
                                "contained in the after validation function, <function "
                                "Contributor.ensure_contact_person_has_email at "
                                "0xADDRESS>."
                            ],
                            "range": "Organization",
                        },
                        {"range": "Software"},
                        {"range": "Agent"},
                    ],
                    "domain_of": ["Activity"],
                }
            },
        )
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Activity"] = Field(
        default="Activity",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class Affiliation(DandiBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "identifier": {
                    "description": "Use an ror.org identifier for " "institutions.",
                    "name": "identifier",
                    "pattern": "^https://ror.org/[a-z0-9]+$",
                    "range": "string",
                    "required": False,
                    "title": "A ror.org identifier",
                },
                "name": {
                    "description": "Name of organization",
                    "name": "name",
                    "required": True,
                },
            },
        }
    )

    identifier: Optional[str] = Field(
        default=None,
        title="A ror.org identifier",
        description="""Use an ror.org identifier for institutions.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    name: str = Field(
        default=...,
        description="""Name of organization""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Affiliation"] = Field(
        default="Affiliation",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )

    @field_validator("identifier")
    def pattern_identifier(cls, v):
        pattern = re.compile(r"^https://ror.org/[a-z0-9]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid identifier format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid identifier format: {v}"
            raise ValueError(err_msg)
        return v


class Agent(DandiBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "identifier": {
                    "description": "Identifier for an agent.",
                    "name": "identifier",
                    "range": "string",
                    "required": False,
                    "title": "Identifier",
                },
                "name": {"name": "name", "required": True},
                "url": {
                    "name": "url",
                    "notes": [
                        "pydantic2linkml: Unable to translate the "
                        "logic contained in the wrap validation "
                        "function, <function "
                        "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                        "at 0xADDRESS>."
                    ],
                    "required": False,
                },
            },
        }
    )

    identifier: Optional[str] = Field(
        default=None,
        title="Identifier",
        description="""Identifier for an agent.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    name: str = Field(
        default=...,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    url: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Agent",
                    "CommonModel",
                    "ContactPoint",
                    "Contributor",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Agent"] = Field(
        default="Agent",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )

    @field_validator("url")
    def pattern_url(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid url format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid url format: {v}"
            raise ValueError(err_msg)
        return v


class Allele(DandiBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "identifier": {
                    "any_of": [
                        {"range": "string"},
                        {"multivalued": True, "range": "string"},
                    ],
                    "description": "Identifier for genotyping " "allele.",
                    "name": "identifier",
                    "range": "Any",
                    "required": True,
                }
            },
        }
    )

    alleleSymbol: Optional[str] = Field(
        default=None, json_schema_extra={"linkml_meta": {"domain_of": ["Allele"]}}
    )
    alleleType: Optional[str] = Field(
        default=None, json_schema_extra={"linkml_meta": {"domain_of": ["Allele"]}}
    )
    identifier: str = Field(
        default=...,
        description="""Identifier for genotyping allele.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {"range": "string"},
                    {"multivalued": True, "range": "string"},
                ],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Allele"] = Field(
        default="Allele",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class AssetsSummary(DandiBaseModel):
    """
    Summary over assets contained in a dandiset (published or not)
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "species": {"multivalued": True, "name": "species"},
                "variableMeasured": {"name": "variableMeasured", "range": "string"},
            },
        }
    )

    approach: Optional[list[ApproachType]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["AssetsSummary", "BareAsset"]}
        },
    )
    dataStandard: Optional[list[StandardsType]] = Field(
        default=None,
        json_schema_extra={"linkml_meta": {"domain_of": ["AssetsSummary"]}},
    )
    measurementTechnique: Optional[list[MeasurementTechniqueType]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["AssetsSummary", "BareAsset"]}
        },
    )
    numberOfBytes: int = Field(
        default=..., json_schema_extra={"linkml_meta": {"domain_of": ["AssetsSummary"]}}
    )
    numberOfCells: Optional[int] = Field(
        default=None,
        json_schema_extra={"linkml_meta": {"domain_of": ["AssetsSummary"]}},
    )
    numberOfFiles: int = Field(
        default=..., json_schema_extra={"linkml_meta": {"domain_of": ["AssetsSummary"]}}
    )
    numberOfSamples: Optional[int] = Field(
        default=None,
        json_schema_extra={"linkml_meta": {"domain_of": ["AssetsSummary"]}},
    )
    numberOfSubjects: Optional[int] = Field(
        default=None,
        json_schema_extra={"linkml_meta": {"domain_of": ["AssetsSummary"]}},
    )
    species: Optional[list[SpeciesType]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["AssetsSummary", "Participant"]}
        },
    )
    variableMeasured: Optional[list[str]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["AssetsSummary", "BareAsset"]}
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["AssetsSummary"] = Field(
        default="AssetsSummary",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class BaseType(DandiBaseModel):
    """
    Base class for enumerated types
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "identifier": {
                    "any_of": [
                        {
                            "notes": [
                                "pydantic2linkml: Unable "
                                "to translate the logic "
                                "contained in the wrap "
                                "validation function, "
                                "<function "
                                "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                                "at 0xADDRESS>."
                            ],
                            "pattern": "^(?i:http|https)://[^\\s]+$",
                            "range": "uri",
                        },
                        {
                            "pattern": "^[a-zA-Z0-9-]+:[a-zA-Z0-9-/\\._]+$",
                            "range": "string",
                        },
                    ],
                    "description": "The identifier can be any url "
                    "or a compact URI, preferably "
                    "supported by identifiers.org.",
                    "name": "identifier",
                    "range": "Any",
                    "required": False,
                },
                "name": {
                    "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                    "description": "The name of the item.",
                    "name": "name",
                    "required": False,
                },
            },
        }
    )

    identifier: Optional[str] = Field(
        default=None,
        description="""The identifier can be any url or a compact URI, preferably supported by identifiers.org.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {
                        "pattern": "^[a-zA-Z0-9-]+:[a-zA-Z0-9-/\\._]+$",
                        "range": "string",
                    },
                ],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    name: Optional[str] = Field(
        default=None,
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["BaseType"] = Field(
        default="BaseType",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class Anatomy(BaseType):
    """
    UBERON or other identifier for anatomical part studied
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7"}
    )

    identifier: Optional[str] = Field(
        default=None,
        description="""The identifier can be any url or a compact URI, preferably supported by identifiers.org.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {
                        "pattern": "^[a-zA-Z0-9-]+:[a-zA-Z0-9-/\\._]+$",
                        "range": "string",
                    },
                ],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    name: Optional[str] = Field(
        default=None,
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Anatomy"] = Field(
        default="Anatomy",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class ApproachType(BaseType):
    """
    Identifier for approach used
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7"}
    )

    identifier: Optional[str] = Field(
        default=None,
        description="""The identifier can be any url or a compact URI, preferably supported by identifiers.org.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {
                        "pattern": "^[a-zA-Z0-9-]+:[a-zA-Z0-9-/\\._]+$",
                        "range": "string",
                    },
                ],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    name: Optional[str] = Field(
        default=None,
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["ApproachType"] = Field(
        default="ApproachType",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class AssayType(BaseType):
    """
    OBI based identifier for the assay(s) used
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7"}
    )

    identifier: Optional[str] = Field(
        default=None,
        description="""The identifier can be any url or a compact URI, preferably supported by identifiers.org.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {
                        "pattern": "^[a-zA-Z0-9-]+:[a-zA-Z0-9-/\\._]+$",
                        "range": "string",
                    },
                ],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    name: Optional[str] = Field(
        default=None,
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["AssayType"] = Field(
        default="AssayType",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class BioSample(DandiBaseModel):
    """
    Description of the sample that was studied
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "identifier": {
                    "name": "identifier",
                    "range": "string",
                    "required": True,
                },
                "sameAs": {"name": "sameAs", "range": "string"},
                "wasAttributedTo": {
                    "description": "Participant(s) or "
                    "Subject(s) associated with "
                    "this sample.",
                    "name": "wasAttributedTo",
                },
                "wasDerivedFrom": {
                    "description": "Describes the hierarchy of "
                    "sample derivation or "
                    "aggregation.",
                    "name": "wasDerivedFrom",
                },
            },
        }
    )

    anatomy: Optional[list[Anatomy]] = Field(
        default=None,
        description="""Identifier for what organ the sample belongs to. Use the most specific descriptor from sources such as UBERON.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["BioSample"]}},
    )
    assayType: Optional[list[AssayType]] = Field(
        default=None,
        description="""Identifier for the assay(s) used (e.g., OBI).""",
        json_schema_extra={"linkml_meta": {"domain_of": ["BioSample"]}},
    )
    hasMember: Optional[list[str]] = Field(
        default=None, json_schema_extra={"linkml_meta": {"domain_of": ["BioSample"]}}
    )
    identifier: str = Field(
        default=...,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    sameAs: Optional[list[str]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BareAsset", "BioSample", "Dandiset", "Participant"]
            }
        },
    )
    sampleType: SampleType = Field(
        default=...,
        description="""Identifier for the sample characteristics (e.g., from OBI, Encode).""",
        json_schema_extra={"linkml_meta": {"domain_of": ["BioSample"]}},
    )
    wasAttributedTo: Optional[list[Participant]] = Field(
        default=None,
        description="""Participant(s) or Subject(s) associated with this sample.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset", "BioSample"]}},
    )
    wasDerivedFrom: Optional[list[BioSample]] = Field(
        default=None,
        description="""Describes the hierarchy of sample derivation or aggregation.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset", "BioSample"]}},
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["BioSample"] = Field(
        default="BioSample",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class CommonModel(DandiBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "access": {
                    "name": "access",
                    "notes": [
                        "pydantic2linkml: Unable to express the "
                        "default factory, <function "
                        "CommonModel.<lambda> at 0xADDRESS>, in "
                        "LinkML.",
                        "pydantic2linkml: Unable to translate the "
                        "logic contained in the after validation "
                        "function, <function "
                        "AccessRequirements.open_or_embargoed at "
                        "0xADDRESS>.",
                    ],
                },
                "contributor": {
                    "description": "Contributors to this item: "
                    "persons or organizations.",
                    "name": "contributor",
                    "required": False,
                    "title": "Contributors",
                },
                "description": {
                    "description": "A description of the item.",
                    "name": "description",
                    "required": False,
                },
                "license": {"name": "license", "required": False},
                "name": {
                    "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                    "description": "The name of the item.",
                    "name": "name",
                    "required": False,
                    "title": "Title",
                },
                "repository": {
                    "description": "location of the item",
                    "name": "repository",
                    "notes": [
                        "pydantic2linkml: Unable to translate "
                        "the logic contained in the wrap "
                        "validation function, <function "
                        "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                        "at 0xADDRESS>."
                    ],
                    "pattern": "^(?i:http|https)://[^\\s]+$",
                    "range": "uri",
                },
                "url": {
                    "description": "permalink to the item",
                    "name": "url",
                    "notes": [
                        "pydantic2linkml: Unable to translate the "
                        "logic contained in the wrap validation "
                        "function, <function "
                        "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                        "at 0xADDRESS>."
                    ],
                    "required": False,
                },
                "wasGeneratedBy": {"name": "wasGeneratedBy", "range": "Activity"},
            },
        }
    )

    about: Optional[list[Union[Anatomy, Disorder, GenericType]]] = Field(
        default=None,
        title="Subject matter of the dataset",
        description="""The subject matter of the content, such as disorders, brain anatomy.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {"range": "Disorder"},
                    {"range": "Anatomy"},
                    {"range": "GenericType"},
                ],
                "domain_of": ["CommonModel"],
            }
        },
    )
    access: Optional[list[AccessRequirements]] = Field(
        default=None,
        title="Access information",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to express the default factory, <function "
                    "CommonModel.<lambda> at 0xADDRESS>, in LinkML.",
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <function "
                    "AccessRequirements.open_or_embargoed at 0xADDRESS>.",
                ],
            }
        },
    )
    acknowledgement: Optional[str] = Field(
        default=None,
        description="""Any acknowledgments not covered by contributors or external resources.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    contributor: Optional[list[Union[Organization, Person]]] = Field(
        default=None,
        title="Contributors",
        description="""Contributors to this item: persons or organizations.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the after validation function, <function "
                            "Contributor.ensure_contact_person_has_email at "
                            "0xADDRESS>."
                        ],
                        "range": "Person",
                    },
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the after validation function, <function "
                            "Contributor.ensure_contact_person_has_email at "
                            "0xADDRESS>."
                        ],
                        "range": "Organization",
                    },
                ],
                "domain_of": ["CommonModel"],
            }
        },
    )
    description: Optional[str] = Field(
        default=None,
        description="""A description of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "AccessRequirements",
                    "Activity",
                    "CommonModel",
                    "Equipment",
                ]
            }
        },
    )
    ethicsApproval: Optional[list[EthicsApproval]] = Field(
        default=None,
        title="Ethics approvals",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    keywords: Optional[list[str]] = Field(
        default=None,
        description="""Keywords used to describe this content.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    license: Optional[list[LicenseType]] = Field(
        default=None,
        description="""Licenses associated with the item. DANDI only supports a subset of Creative Commons Licenses (creativecommons.org) applicable to datasets.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    name: Optional[str] = Field(
        default=None,
        title="Title",
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    protocol: Optional[list[str]] = Field(
        default=None,
        description="""A list of persistent URLs describing the protocol (e.g. protocols.io, or other DOIs).""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    relatedResource: Optional[list[Resource]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <function Resource.identifier_or_url at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    repository: Optional[str] = Field(
        default=None,
        description="""location of the item""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel", "Resource"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    schemaVersion: Optional[str] = Field(
        default="0.7.0",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["CommonModel"], "ifabsent": "string(0.7.0)"}
        },
    )
    studyTarget: Optional[list[str]] = Field(
        default=None,
        description="""Objectives or specific questions of the study.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    url: Optional[str] = Field(
        default=None,
        description="""permalink to the item""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Agent",
                    "CommonModel",
                    "ContactPoint",
                    "Contributor",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    wasGeneratedBy: Optional[
        list[Union[Activity, Project, PublishActivity, Session]]
    ] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["CommonModel", "GenotypeInfo"]}
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["CommonModel"] = Field(
        default="CommonModel",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )

    @field_validator("protocol")
    def pattern_protocol(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid protocol format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid protocol format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("repository")
    def pattern_repository(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid repository format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid repository format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("url")
    def pattern_url(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid url format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid url format: {v}"
            raise ValueError(err_msg)
        return v


class BareAsset(CommonModel):
    """
    Metadata used to describe an asset anywhere (local or server). Derived from C2M2 (Level 0 and 1) and schema.org
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "notes": [
                "pydantic2linkml: Impossible to generate slot usage entry for the "
                "wasGeneratedBy slot. The slot representation of the wasGeneratedBy "
                "field in the BareAsset Pydantic model has changes in value in "
                "constraint meta slots: ['range'] .",
                "MANUAL_NOTE: The default of the `schemaKey` field in the "
                "corresponding Pydantic model in `dandischema.models` is not the "
                "model's name. Adjustment to the inherited `schemaKey` slot may be "
                "needed.",
            ],
            "slot_usage": {
                "access": {
                    "maximum_cardinality": 1,
                    "name": "access",
                    "notes": [
                        "pydantic2linkml: Unable to express the "
                        "default factory, <function "
                        "BareAsset.<lambda> at 0xADDRESS>, in "
                        "LinkML.",
                        "pydantic2linkml: Unable to translate the "
                        "logic contained in the after validation "
                        "function, <function "
                        "AccessRequirements.open_or_embargoed at "
                        "0xADDRESS>.",
                    ],
                },
                "dateModified": {
                    "name": "dateModified",
                    "title": "Asset (file or metadata) " "modification date and time",
                },
                "sameAs": {
                    "name": "sameAs",
                    "notes": [
                        "pydantic2linkml: Unable to translate the "
                        "logic contained in the wrap validation "
                        "function, <function "
                        "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                        "at 0xADDRESS>."
                    ],
                    "pattern": "^(?i:http|https)://[^\\s]+$",
                    "range": "uri",
                },
                "variableMeasured": {
                    "name": "variableMeasured",
                    "range": "PropertyValue",
                },
                "wasAttributedTo": {
                    "description": "Associated participant(s) " "or subject(s).",
                    "name": "wasAttributedTo",
                },
            },
        }
    )

    approach: Optional[list[ApproachType]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["AssetsSummary", "BareAsset"]}
        },
    )
    blobDateModified: Optional[datetime] = Field(
        default=None,
        title="Asset file modification date and time.",
        json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset"]}},
    )
    contentSize: Union[int, str] = Field(
        default=...,
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {"pattern": "^\\s*(\\d*\\.?\\d+)\\s*(\\w+)?", "range": "string"},
                    {"minimum_value": 0, "range": "integer"},
                ],
                "domain_of": ["BareAsset"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <bound method ByteSize._validate of "
                    "<class 'pydantic.types.ByteSize'>>."
                ],
            }
        },
    )
    dataType: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BareAsset"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    dateModified: Optional[datetime] = Field(
        default=None,
        title="Asset (file or metadata) modification date and time",
        json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset", "Dandiset"]}},
    )
    digest: str = Field(
        default=...,
        title="A map of dandi digests to their values",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BareAsset"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <bound method BareAsset.digest_check of "
                    "<class 'dandischema.models.BareAsset'>>.",
                    "pydantic2linkml: Warning: The translation is incomplete. `dict` "
                    "types are yet to be supported.",
                ],
            }
        },
    )
    encodingFormat: str = Field(
        default=...,
        title="File encoding format",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {"range": "string"},
                ],
                "domain_of": ["BareAsset"],
            }
        },
    )
    measurementTechnique: Optional[list[MeasurementTechniqueType]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["AssetsSummary", "BareAsset"]}
        },
    )
    path: str = Field(
        default=..., json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset"]}}
    )
    sameAs: Optional[list[str]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BareAsset", "BioSample", "Dandiset", "Participant"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    variableMeasured: Optional[list[PropertyValue]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["AssetsSummary", "BareAsset"]}
        },
    )
    wasAttributedTo: Optional[list[Participant]] = Field(
        default=None,
        description="""Associated participant(s) or subject(s).""",
        json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset", "BioSample"]}},
    )
    wasDerivedFrom: Optional[list[BioSample]] = Field(
        default=None,
        json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset", "BioSample"]}},
    )
    about: Optional[list[Union[Anatomy, Disorder, GenericType]]] = Field(
        default=None,
        title="Subject matter of the dataset",
        description="""The subject matter of the content, such as disorders, brain anatomy.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {"range": "Disorder"},
                    {"range": "Anatomy"},
                    {"range": "GenericType"},
                ],
                "domain_of": ["CommonModel"],
            }
        },
    )
    access: Optional[list[AccessRequirements]] = Field(
        default=None,
        title="Access information",
        max_length=1,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to express the default factory, <function "
                    "BareAsset.<lambda> at 0xADDRESS>, in LinkML.",
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <function "
                    "AccessRequirements.open_or_embargoed at 0xADDRESS>.",
                ],
            }
        },
    )
    acknowledgement: Optional[str] = Field(
        default=None,
        description="""Any acknowledgments not covered by contributors or external resources.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    contributor: Optional[list[Union[Organization, Person]]] = Field(
        default=None,
        title="Contributors",
        description="""Contributors to this item: persons or organizations.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the after validation function, <function "
                            "Contributor.ensure_contact_person_has_email at "
                            "0xADDRESS>."
                        ],
                        "range": "Person",
                    },
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the after validation function, <function "
                            "Contributor.ensure_contact_person_has_email at "
                            "0xADDRESS>."
                        ],
                        "range": "Organization",
                    },
                ],
                "domain_of": ["CommonModel"],
            }
        },
    )
    description: Optional[str] = Field(
        default=None,
        description="""A description of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "AccessRequirements",
                    "Activity",
                    "CommonModel",
                    "Equipment",
                ]
            }
        },
    )
    ethicsApproval: Optional[list[EthicsApproval]] = Field(
        default=None,
        title="Ethics approvals",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    keywords: Optional[list[str]] = Field(
        default=None,
        description="""Keywords used to describe this content.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    license: Optional[list[LicenseType]] = Field(
        default=None,
        description="""Licenses associated with the item. DANDI only supports a subset of Creative Commons Licenses (creativecommons.org) applicable to datasets.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    name: Optional[str] = Field(
        default=None,
        title="Title",
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    protocol: Optional[list[str]] = Field(
        default=None,
        description="""A list of persistent URLs describing the protocol (e.g. protocols.io, or other DOIs).""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    relatedResource: Optional[list[Resource]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <function Resource.identifier_or_url at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    repository: Optional[str] = Field(
        default=None,
        description="""location of the item""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel", "Resource"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    schemaVersion: Optional[str] = Field(
        default="0.7.0",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["CommonModel"], "ifabsent": "string(0.7.0)"}
        },
    )
    studyTarget: Optional[list[str]] = Field(
        default=None,
        description="""Objectives or specific questions of the study.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    url: Optional[str] = Field(
        default=None,
        description="""permalink to the item""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Agent",
                    "CommonModel",
                    "ContactPoint",
                    "Contributor",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    wasGeneratedBy: Optional[
        list[Union[Activity, Project, PublishActivity, Session]]
    ] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["CommonModel", "GenotypeInfo"]}
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["BareAsset"] = Field(
        default="BareAsset",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )

    @field_validator("dataType")
    def pattern_dataType(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid dataType format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid dataType format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("sameAs")
    def pattern_sameAs(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid sameAs format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid sameAs format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("protocol")
    def pattern_protocol(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid protocol format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid protocol format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("repository")
    def pattern_repository(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid repository format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid repository format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("url")
    def pattern_url(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid url format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid url format: {v}"
            raise ValueError(err_msg)
        return v


class Asset(BareAsset):
    """
    Metadata used to describe an asset on the server.
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "notes": [
                "pydantic2linkml: Impossible to generate slot usage entry for the "
                "id slot. The slot representation of the id field in the Asset "
                "Pydantic model has changes in value in constraint meta slots: "
                "['required'] ."
            ],
            "slot_usage": {
                "identifier": {
                    "name": "identifier",
                    "pattern": "^(?:urn:uuid:)?[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?4[0-9a-fA-F]{3}-?[89abAB][0-9a-fA-F]{3}-?[0-9a-fA-F]{12}$",
                    "range": "string",
                    "required": True,
                }
            },
        }
    )

    contentUrl: list[str] = Field(
        default=...,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["Asset"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    identifier: str = Field(
        default=...,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    approach: Optional[list[ApproachType]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["AssetsSummary", "BareAsset"]}
        },
    )
    blobDateModified: Optional[datetime] = Field(
        default=None,
        title="Asset file modification date and time.",
        json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset"]}},
    )
    contentSize: Union[int, str] = Field(
        default=...,
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {"pattern": "^\\s*(\\d*\\.?\\d+)\\s*(\\w+)?", "range": "string"},
                    {"minimum_value": 0, "range": "integer"},
                ],
                "domain_of": ["BareAsset"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <bound method ByteSize._validate of "
                    "<class 'pydantic.types.ByteSize'>>."
                ],
            }
        },
    )
    dataType: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BareAsset"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    dateModified: Optional[datetime] = Field(
        default=None,
        title="Asset (file or metadata) modification date and time",
        json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset", "Dandiset"]}},
    )
    digest: str = Field(
        default=...,
        title="A map of dandi digests to their values",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BareAsset"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <bound method BareAsset.digest_check of "
                    "<class 'dandischema.models.BareAsset'>>.",
                    "pydantic2linkml: Warning: The translation is incomplete. `dict` "
                    "types are yet to be supported.",
                ],
            }
        },
    )
    encodingFormat: str = Field(
        default=...,
        title="File encoding format",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {"range": "string"},
                ],
                "domain_of": ["BareAsset"],
            }
        },
    )
    measurementTechnique: Optional[list[MeasurementTechniqueType]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["AssetsSummary", "BareAsset"]}
        },
    )
    path: str = Field(
        default=..., json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset"]}}
    )
    sameAs: Optional[list[str]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BareAsset", "BioSample", "Dandiset", "Participant"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    variableMeasured: Optional[list[PropertyValue]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["AssetsSummary", "BareAsset"]}
        },
    )
    wasAttributedTo: Optional[list[Participant]] = Field(
        default=None,
        description="""Associated participant(s) or subject(s).""",
        json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset", "BioSample"]}},
    )
    wasDerivedFrom: Optional[list[BioSample]] = Field(
        default=None,
        json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset", "BioSample"]}},
    )
    about: Optional[list[Union[Anatomy, Disorder, GenericType]]] = Field(
        default=None,
        title="Subject matter of the dataset",
        description="""The subject matter of the content, such as disorders, brain anatomy.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {"range": "Disorder"},
                    {"range": "Anatomy"},
                    {"range": "GenericType"},
                ],
                "domain_of": ["CommonModel"],
            }
        },
    )
    access: Optional[list[AccessRequirements]] = Field(
        default=None,
        title="Access information",
        max_length=1,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to express the default factory, <function "
                    "BareAsset.<lambda> at 0xADDRESS>, in LinkML.",
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <function "
                    "AccessRequirements.open_or_embargoed at 0xADDRESS>.",
                ],
            }
        },
    )
    acknowledgement: Optional[str] = Field(
        default=None,
        description="""Any acknowledgments not covered by contributors or external resources.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    contributor: Optional[list[Union[Organization, Person]]] = Field(
        default=None,
        title="Contributors",
        description="""Contributors to this item: persons or organizations.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the after validation function, <function "
                            "Contributor.ensure_contact_person_has_email at "
                            "0xADDRESS>."
                        ],
                        "range": "Person",
                    },
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the after validation function, <function "
                            "Contributor.ensure_contact_person_has_email at "
                            "0xADDRESS>."
                        ],
                        "range": "Organization",
                    },
                ],
                "domain_of": ["CommonModel"],
            }
        },
    )
    description: Optional[str] = Field(
        default=None,
        description="""A description of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "AccessRequirements",
                    "Activity",
                    "CommonModel",
                    "Equipment",
                ]
            }
        },
    )
    ethicsApproval: Optional[list[EthicsApproval]] = Field(
        default=None,
        title="Ethics approvals",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    keywords: Optional[list[str]] = Field(
        default=None,
        description="""Keywords used to describe this content.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    license: Optional[list[LicenseType]] = Field(
        default=None,
        description="""Licenses associated with the item. DANDI only supports a subset of Creative Commons Licenses (creativecommons.org) applicable to datasets.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    name: Optional[str] = Field(
        default=None,
        title="Title",
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    protocol: Optional[list[str]] = Field(
        default=None,
        description="""A list of persistent URLs describing the protocol (e.g. protocols.io, or other DOIs).""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    relatedResource: Optional[list[Resource]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <function Resource.identifier_or_url at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    repository: Optional[str] = Field(
        default=None,
        description="""location of the item""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel", "Resource"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    schemaVersion: Optional[str] = Field(
        default="0.7.0",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["CommonModel"], "ifabsent": "string(0.7.0)"}
        },
    )
    studyTarget: Optional[list[str]] = Field(
        default=None,
        description="""Objectives or specific questions of the study.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    url: Optional[str] = Field(
        default=None,
        description="""permalink to the item""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Agent",
                    "CommonModel",
                    "ContactPoint",
                    "Contributor",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    wasGeneratedBy: Optional[
        list[Union[Activity, Project, PublishActivity, Session]]
    ] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["CommonModel", "GenotypeInfo"]}
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Asset"] = Field(
        default="Asset",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )

    @field_validator("contentUrl")
    def pattern_contentUrl(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid contentUrl format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid contentUrl format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("identifier")
    def pattern_identifier(cls, v):
        pattern = re.compile(
            r"^(?:urn:uuid:)?[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?4[0-9a-fA-F]{3}-?[89abAB][0-9a-fA-F]{3}-?[0-9a-fA-F]{12}$"
        )
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid identifier format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid identifier format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("dataType")
    def pattern_dataType(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid dataType format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid dataType format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("sameAs")
    def pattern_sameAs(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid sameAs format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid sameAs format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("protocol")
    def pattern_protocol(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid protocol format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid protocol format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("repository")
    def pattern_repository(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid repository format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid repository format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("url")
    def pattern_url(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid url format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid url format: {v}"
            raise ValueError(err_msg)
        return v


class ContactPoint(DandiBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "email": {"description": "Email address of contact.", "name": "email"},
                "url": {
                    "description": "A Web page to find information on how "
                    "to contact.",
                    "name": "url",
                    "notes": [
                        "pydantic2linkml: Unable to translate the "
                        "logic contained in the wrap validation "
                        "function, <function "
                        "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                        "at 0xADDRESS>."
                    ],
                    "required": False,
                },
            },
        }
    )

    email: Optional[str] = Field(
        default=None,
        description="""Email address of contact.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["ContactPoint", "Contributor"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <bound method EmailStr._validate of "
                    "<class 'pydantic.networks.EmailStr'>>."
                ],
            }
        },
    )
    url: Optional[str] = Field(
        default=None,
        description="""A Web page to find information on how to contact.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Agent",
                    "CommonModel",
                    "ContactPoint",
                    "Contributor",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["ContactPoint"] = Field(
        default="ContactPoint",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )

    @field_validator("url")
    def pattern_url(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid url format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid url format: {v}"
            raise ValueError(err_msg)
        return v


class Contributor(DandiBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "identifier": {
                    "description": "Use a common identifier such as "
                    "ORCID (orcid.org) for people or "
                    "ROR (ror.org) for institutions.",
                    "name": "identifier",
                    "range": "string",
                    "required": False,
                    "title": "A common identifier",
                },
                "includeInCitation": {
                    "description": "A flag to indicate "
                    "whether a contributor "
                    "should be included when "
                    "generating a citation "
                    "for the item.",
                    "ifabsent": "True",
                    "name": "includeInCitation",
                },
                "name": {"name": "name", "required": False},
                "url": {
                    "name": "url",
                    "notes": [
                        "pydantic2linkml: Unable to translate the "
                        "logic contained in the wrap validation "
                        "function, <function "
                        "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                        "at 0xADDRESS>."
                    ],
                    "required": False,
                },
            },
        }
    )

    awardNumber: Optional[str] = Field(
        default=None,
        title="Identifier for an award",
        description="""Identifier associated with a sponsored or gift award.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Contributor"]}},
    )
    email: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["ContactPoint", "Contributor"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <bound method EmailStr._validate of "
                    "<class 'pydantic.networks.EmailStr'>>."
                ],
            }
        },
    )
    identifier: Optional[str] = Field(
        default=None,
        title="A common identifier",
        description="""Use a common identifier such as ORCID (orcid.org) for people or ROR (ror.org) for institutions.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    includeInCitation: Optional[bool] = Field(
        default=True,
        title="Include contributor in citation",
        description="""A flag to indicate whether a contributor should be included when generating a citation for the item.""",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["Contributor"], "ifabsent": "True"}
        },
    )
    name: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    roleName: Optional[list[RoleType]] = Field(
        default=None,
        title="Role",
        description="""Role(s) of the contributor. Multiple roles can be selected.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Contributor"]}},
    )
    url: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Agent",
                    "CommonModel",
                    "ContactPoint",
                    "Contributor",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Contributor"] = Field(
        default="Contributor",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )

    @field_validator("url")
    def pattern_url(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid url format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid url format: {v}"
            raise ValueError(err_msg)
        return v


class Dandiset(CommonModel):
    """
    A body of structured information describing a DANDI dataset.
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "notes": [
                "pydantic2linkml: Impossible to generate slot usage entry for the "
                "contributor slot. The slot representation of the contributor field "
                "in the Dandiset Pydantic model has changes in value in constraint "
                "meta slots: ['required'] .",
                "pydantic2linkml: Impossible to generate slot usage entry for the "
                "description slot. The slot representation of the description field "
                "in the Dandiset Pydantic model has changes in value in constraint "
                "meta slots: ['required'] .",
                "pydantic2linkml: Impossible to generate slot usage entry for the "
                "id slot. The slot representation of the id field in the Dandiset "
                "Pydantic model has changes in value in constraint meta slots: "
                "['required'] .",
                "pydantic2linkml: Impossible to generate slot usage entry for the "
                "license slot. The slot representation of the license field in the "
                "Dandiset Pydantic model has changes in value in constraint meta "
                "slots: ['required'] .",
                "pydantic2linkml: Impossible to generate slot usage entry for the "
                "name slot. The slot representation of the name field in the "
                "Dandiset Pydantic model has changes in value in constraint meta "
                "slots: ['required'] .",
                "pydantic2linkml: Impossible to generate slot usage entry for the "
                "wasGeneratedBy slot. The slot representation of the wasGeneratedBy "
                "field in the Dandiset Pydantic model has changes in value in "
                "constraint meta slots: ['range'] .",
            ],
            "slot_usage": {
                "dateModified": {
                    "name": "dateModified",
                    "title": "Last modification date and time.",
                },
                "identifier": {
                    "description": "A Dandiset identifier that can "
                    "be resolved by identifiers.org.",
                    "name": "identifier",
                    "pattern": "^[A-Z][-A-Z]*:\\d{6}$",
                    "range": "string",
                    "required": True,
                    "title": "Dandiset identifier",
                },
                "sameAs": {
                    "description": "Known DANDI URLs of the Dandiset at "
                    "other DANDI instances.",
                    "name": "sameAs",
                    "pattern": "^dandi://[A-Z][-A-Z]*/\\d{6}(@(draft|\\d+\\.\\d+\\.\\d+))?(/\\S+)?$",
                    "range": "string",
                },
            },
        }
    )

    assetsSummary: AssetsSummary = Field(
        default=..., json_schema_extra={"linkml_meta": {"domain_of": ["Dandiset"]}}
    )
    citation: str = Field(
        default=..., json_schema_extra={"linkml_meta": {"domain_of": ["Dandiset"]}}
    )
    dateCreated: Optional[datetime] = Field(
        default=None,
        title="Dandiset creation date and time.",
        json_schema_extra={"linkml_meta": {"domain_of": ["Dandiset"]}},
    )
    dateModified: Optional[datetime] = Field(
        default=None,
        title="Last modification date and time.",
        json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset", "Dandiset"]}},
    )
    identifier: str = Field(
        default=...,
        title="Dandiset identifier",
        description="""A Dandiset identifier that can be resolved by identifiers.org.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    manifestLocation: list[str] = Field(
        default=...,
        min_length=1,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["Dandiset"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    sameAs: Optional[list[str]] = Field(
        default=None,
        description="""Known DANDI URLs of the Dandiset at other DANDI instances.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BareAsset", "BioSample", "Dandiset", "Participant"]
            }
        },
    )
    version: str = Field(
        default=...,
        json_schema_extra={"linkml_meta": {"domain_of": ["Dandiset", "Software"]}},
    )
    about: Optional[list[Union[Anatomy, Disorder, GenericType]]] = Field(
        default=None,
        title="Subject matter of the dataset",
        description="""The subject matter of the content, such as disorders, brain anatomy.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {"range": "Disorder"},
                    {"range": "Anatomy"},
                    {"range": "GenericType"},
                ],
                "domain_of": ["CommonModel"],
            }
        },
    )
    access: Optional[list[AccessRequirements]] = Field(
        default=None,
        title="Access information",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to express the default factory, <function "
                    "CommonModel.<lambda> at 0xADDRESS>, in LinkML.",
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <function "
                    "AccessRequirements.open_or_embargoed at 0xADDRESS>.",
                ],
            }
        },
    )
    acknowledgement: Optional[str] = Field(
        default=None,
        description="""Any acknowledgments not covered by contributors or external resources.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    contributor: Optional[list[Union[Organization, Person]]] = Field(
        default=None,
        title="Contributors",
        description="""Contributors to this item: persons or organizations.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the after validation function, <function "
                            "Contributor.ensure_contact_person_has_email at "
                            "0xADDRESS>."
                        ],
                        "range": "Person",
                    },
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the after validation function, <function "
                            "Contributor.ensure_contact_person_has_email at "
                            "0xADDRESS>."
                        ],
                        "range": "Organization",
                    },
                ],
                "domain_of": ["CommonModel"],
            }
        },
    )
    description: Optional[str] = Field(
        default=None,
        description="""A description of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "AccessRequirements",
                    "Activity",
                    "CommonModel",
                    "Equipment",
                ]
            }
        },
    )
    ethicsApproval: Optional[list[EthicsApproval]] = Field(
        default=None,
        title="Ethics approvals",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    keywords: Optional[list[str]] = Field(
        default=None,
        description="""Keywords used to describe this content.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    license: Optional[list[LicenseType]] = Field(
        default=None,
        description="""Licenses associated with the item. DANDI only supports a subset of Creative Commons Licenses (creativecommons.org) applicable to datasets.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    name: Optional[str] = Field(
        default=None,
        title="Title",
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    protocol: Optional[list[str]] = Field(
        default=None,
        description="""A list of persistent URLs describing the protocol (e.g. protocols.io, or other DOIs).""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    relatedResource: Optional[list[Resource]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <function Resource.identifier_or_url at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    repository: Optional[str] = Field(
        default=None,
        description="""location of the item""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel", "Resource"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    schemaVersion: Optional[str] = Field(
        default="0.7.0",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["CommonModel"], "ifabsent": "string(0.7.0)"}
        },
    )
    studyTarget: Optional[list[str]] = Field(
        default=None,
        description="""Objectives or specific questions of the study.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    url: Optional[str] = Field(
        default=None,
        description="""permalink to the item""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Agent",
                    "CommonModel",
                    "ContactPoint",
                    "Contributor",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    wasGeneratedBy: Optional[
        list[Union[Activity, Project, PublishActivity, Session]]
    ] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["CommonModel", "GenotypeInfo"]}
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Dandiset"] = Field(
        default="Dandiset",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )

    @field_validator("identifier")
    def pattern_identifier(cls, v):
        pattern = re.compile(r"^[A-Z][-A-Z]*:\d{6}$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid identifier format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid identifier format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("manifestLocation")
    def pattern_manifestLocation(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid manifestLocation format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid manifestLocation format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("sameAs")
    def pattern_sameAs(cls, v):
        pattern = re.compile(
            r"^dandi://[A-Z][-A-Z]*/\d{6}(@(draft|\d+\.\d+\.\d+))?(/\S+)?$"
        )
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid sameAs format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid sameAs format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("protocol")
    def pattern_protocol(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid protocol format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid protocol format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("repository")
    def pattern_repository(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid repository format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid repository format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("url")
    def pattern_url(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid url format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid url format: {v}"
            raise ValueError(err_msg)
        return v


class Disorder(BaseType):
    """
    Biolink, SNOMED, or other identifier for disorder studied
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7"}
    )

    dxdate: Optional[list[Union[date, datetime]]] = Field(
        default=None,
        title="Dates of diagnosis",
        description="""Dates of diagnosis""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [{"range": "date"}, {"range": "datetime"}],
                "domain_of": ["Disorder"],
            }
        },
    )
    identifier: Optional[str] = Field(
        default=None,
        description="""The identifier can be any url or a compact URI, preferably supported by identifiers.org.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {
                        "pattern": "^[a-zA-Z0-9-]+:[a-zA-Z0-9-/\\._]+$",
                        "range": "string",
                    },
                ],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    name: Optional[str] = Field(
        default=None,
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Disorder"] = Field(
        default="Disorder",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class Equipment(DandiBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "description": {
                    "description": "The description of the " "equipment.",
                    "name": "description",
                    "required": False,
                },
                "identifier": {
                    "name": "identifier",
                    "range": "string",
                    "required": False,
                },
                "name": {
                    "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                    "description": "A name for the equipment.",
                    "name": "name",
                    "required": True,
                    "title": "Title",
                },
            },
        }
    )

    description: Optional[str] = Field(
        default=None,
        description="""The description of the equipment.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "AccessRequirements",
                    "Activity",
                    "CommonModel",
                    "Equipment",
                ]
            }
        },
    )
    identifier: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    name: str = Field(
        default=...,
        title="Title",
        description="""A name for the equipment.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Equipment"] = Field(
        default="Equipment",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class EthicsApproval(DandiBaseModel):
    """
    Information about ethics committee approval for project
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "contactPoint": {
                    "description": "Information about the ethics "
                    "approval committee.",
                    "name": "contactPoint",
                },
                "identifier": {
                    "description": "Approved Protocol identifier, "
                    "often a number or alphanumeric "
                    "string.",
                    "name": "identifier",
                    "range": "string",
                    "required": True,
                    "title": "Approved protocol identifier",
                },
            },
        }
    )

    contactPoint: Optional[ContactPoint] = Field(
        default=None,
        description="""Information about the ethics approval committee.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["AccessRequirements", "EthicsApproval", "Organization"]
            }
        },
    )
    identifier: str = Field(
        default=...,
        title="Approved protocol identifier",
        description="""Approved Protocol identifier, often a number or alphanumeric string.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["EthicsApproval"] = Field(
        default="EthicsApproval",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class GenericType(BaseType):
    """
    An object to capture any type for about
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7"}
    )

    identifier: Optional[str] = Field(
        default=None,
        description="""The identifier can be any url or a compact URI, preferably supported by identifiers.org.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {
                        "pattern": "^[a-zA-Z0-9-]+:[a-zA-Z0-9-/\\._]+$",
                        "range": "string",
                    },
                ],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    name: Optional[str] = Field(
        default=None,
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["GenericType"] = Field(
        default="GenericType",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class GenotypeInfo(DandiBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "wasGeneratedBy": {
                    "description": "Information about session "
                    "activity used to determine "
                    "genotype.",
                    "name": "wasGeneratedBy",
                    "range": "Session",
                }
            },
        }
    )

    alleles: list[Allele] = Field(
        default=...,
        description="""Information about alleles at the locus.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["GenotypeInfo"]}},
    )
    locus: Locus = Field(
        default=...,
        description="""Locus at which information was extracted.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["GenotypeInfo"]}},
    )
    wasGeneratedBy: Optional[list[Session]] = Field(
        default=None,
        description="""Information about session activity used to determine genotype.""",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["CommonModel", "GenotypeInfo"]}
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["GenotypeInfo"] = Field(
        default="GenotypeInfo",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class Locus(DandiBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "identifier": {
                    "any_of": [
                        {"range": "string"},
                        {"multivalued": True, "range": "string"},
                    ],
                    "description": "Identifier for genotyping " "locus.",
                    "name": "identifier",
                    "range": "Any",
                    "required": True,
                }
            },
        }
    )

    identifier: str = Field(
        default=...,
        description="""Identifier for genotyping locus.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {"range": "string"},
                    {"multivalued": True, "range": "string"},
                ],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    locusType: Optional[str] = Field(
        default=None, json_schema_extra={"linkml_meta": {"domain_of": ["Locus"]}}
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Locus"] = Field(
        default="Locus",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class MeasurementTechniqueType(BaseType):
    """
    Identifier for measurement technique used
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7"}
    )

    identifier: Optional[str] = Field(
        default=None,
        description="""The identifier can be any url or a compact URI, preferably supported by identifiers.org.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {
                        "pattern": "^[a-zA-Z0-9-]+:[a-zA-Z0-9-/\\._]+$",
                        "range": "string",
                    },
                ],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    name: Optional[str] = Field(
        default=None,
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["MeasurementTechniqueType"] = Field(
        default="MeasurementTechniqueType",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class Organization(Contributor):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "contactPoint": {
                    "description": "Contact for the organization",
                    "multivalued": True,
                    "name": "contactPoint",
                    "title": "Organization contact information",
                },
                "identifier": {
                    "description": "Use an ror.org identifier for " "institutions.",
                    "name": "identifier",
                    "pattern": "^https://ror.org/[a-z0-9]+$",
                    "title": "A ror.org identifier",
                },
                "includeInCitation": {
                    "description": "A flag to indicate "
                    "whether a contributor "
                    "should be included when "
                    "generating a citation "
                    "for the item",
                    "ifabsent": "False",
                    "name": "includeInCitation",
                },
            },
        }
    )

    contactPoint: Optional[list[ContactPoint]] = Field(
        default=None,
        title="Organization contact information",
        description="""Contact for the organization""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["AccessRequirements", "EthicsApproval", "Organization"]
            }
        },
    )
    awardNumber: Optional[str] = Field(
        default=None,
        title="Identifier for an award",
        description="""Identifier associated with a sponsored or gift award.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Contributor"]}},
    )
    email: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["ContactPoint", "Contributor"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <bound method EmailStr._validate of "
                    "<class 'pydantic.networks.EmailStr'>>."
                ],
            }
        },
    )
    identifier: Optional[str] = Field(
        default=None,
        title="A ror.org identifier",
        description="""Use an ror.org identifier for institutions.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    includeInCitation: Optional[bool] = Field(
        default=False,
        title="Include contributor in citation",
        description="""A flag to indicate whether a contributor should be included when generating a citation for the item""",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["Contributor"], "ifabsent": "False"}
        },
    )
    name: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    roleName: Optional[list[RoleType]] = Field(
        default=None,
        title="Role",
        description="""Role(s) of the contributor. Multiple roles can be selected.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Contributor"]}},
    )
    url: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Agent",
                    "CommonModel",
                    "ContactPoint",
                    "Contributor",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Organization"] = Field(
        default="Organization",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )

    @field_validator("identifier")
    def pattern_identifier(cls, v):
        pattern = re.compile(r"^https://ror.org/[a-z0-9]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid identifier format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid identifier format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("url")
    def pattern_url(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid url format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid url format: {v}"
            raise ValueError(err_msg)
        return v


class Participant(DandiBaseModel):
    """
    Description about the Participant or Subject studied. The Participant or Subject can be any individual or synthesized Agent. The properties of the Participant or Subject refers to information at the timepoint when the Participant or Subject engaged in the production of data being described.
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "identifier": {
                    "name": "identifier",
                    "range": "string",
                    "required": True,
                },
                "sameAs": {
                    "description": "An identifier to link participants "
                    "or subjects across datasets.",
                    "name": "sameAs",
                    "range": "string",
                },
                "species": {
                    "description": "An identifier indicating the "
                    "taxonomic classification of the "
                    "participant or subject.",
                    "name": "species",
                },
            },
        }
    )

    age: Optional[PropertyValue] = Field(
        default=None,
        description="""A representation of age using ISO 8601 duration. This should include a valueReference if anything other than date of birth is used.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Participant"]}},
    )
    altName: Optional[list[str]] = Field(
        default=None, json_schema_extra={"linkml_meta": {"domain_of": ["Participant"]}}
    )
    cellLine: Optional[str] = Field(
        default=None,
        description="""Cell line associated with the participant or subject.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Participant"]}},
    )
    disorder: Optional[list[Disorder]] = Field(
        default=None,
        description="""Any current diagnosed disease or disorder associated with the participant or subject.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Participant"]}},
    )
    genotype: Optional[Union[GenotypeInfo, str]] = Field(
        default=None,
        description="""Genotype descriptor of participant or subject if available""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {"multivalued": True, "range": "GenotypeInfo"},
                    {"range": "string"},
                ],
                "domain_of": ["Participant"],
            }
        },
    )
    identifier: str = Field(
        default=...,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    relatedParticipant: Optional[list[RelatedParticipant]] = Field(
        default=None,
        description="""Information about related participants or subjects in a study or across studies.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Participant"]}},
    )
    sameAs: Optional[list[str]] = Field(
        default=None,
        description="""An identifier to link participants or subjects across datasets.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BareAsset", "BioSample", "Dandiset", "Participant"]
            }
        },
    )
    sex: Optional[SexType] = Field(
        default=None,
        description="""Identifier for sex of the participant or subject if available. (e.g. from OBI)""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Participant"]}},
    )
    species: Optional[SpeciesType] = Field(
        default=None,
        description="""An identifier indicating the taxonomic classification of the participant or subject.""",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["AssetsSummary", "Participant"]}
        },
    )
    strain: Optional[StrainType] = Field(
        default=None,
        description="""Identifier for the strain of the participant or subject.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Participant"]}},
    )
    vendor: Optional[Organization] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["Participant"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <function "
                    "Contributor.ensure_contact_person_has_email at 0xADDRESS>."
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Participant"] = Field(
        default="Participant",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class Person(Contributor):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "notes": [
                "pydantic2linkml: Impossible to generate slot usage entry for the "
                "name slot. The slot representation of the name field in the Person "
                "Pydantic model has changes in value in constraint meta slots: "
                "['required'] ."
            ],
            "slot_usage": {
                "identifier": {
                    "description": "An ORCID (orcid.org) identifier "
                    "for an individual.",
                    "name": "identifier",
                    "pattern": "^\\d{4}-\\d{4}-\\d{4}-(\\d{3}X|\\d{4})$",
                    "title": "An ORCID identifier",
                }
            },
        }
    )

    affiliation: Optional[list[Affiliation]] = Field(
        default=None,
        description="""An organization that this person is affiliated with.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Person"]}},
    )
    awardNumber: Optional[str] = Field(
        default=None,
        title="Identifier for an award",
        description="""Identifier associated with a sponsored or gift award.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Contributor"]}},
    )
    email: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["ContactPoint", "Contributor"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <bound method EmailStr._validate of "
                    "<class 'pydantic.networks.EmailStr'>>."
                ],
            }
        },
    )
    identifier: Optional[str] = Field(
        default=None,
        title="An ORCID identifier",
        description="""An ORCID (orcid.org) identifier for an individual.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    includeInCitation: Optional[bool] = Field(
        default=True,
        title="Include contributor in citation",
        description="""A flag to indicate whether a contributor should be included when generating a citation for the item.""",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["Contributor"], "ifabsent": "True"}
        },
    )
    name: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    roleName: Optional[list[RoleType]] = Field(
        default=None,
        title="Role",
        description="""Role(s) of the contributor. Multiple roles can be selected.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Contributor"]}},
    )
    url: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Agent",
                    "CommonModel",
                    "ContactPoint",
                    "Contributor",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Person"] = Field(
        default="Person",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )

    @field_validator("identifier")
    def pattern_identifier(cls, v):
        pattern = re.compile(r"^\d{4}-\d{4}-\d{4}-(\d{3}X|\d{4})$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid identifier format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid identifier format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("url")
    def pattern_url(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid url format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid url format: {v}"
            raise ValueError(err_msg)
        return v


class Project(Activity):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "description": {
                    "description": "A brief description of the " "project.",
                    "name": "description",
                },
                "name": {
                    "description": "The name of the project that "
                    "generated this Dandiset or asset.",
                    "name": "name",
                    "title": "Name of project",
                },
            },
        }
    )

    description: Optional[str] = Field(
        default=None,
        description="""A brief description of the project.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "AccessRequirements",
                    "Activity",
                    "CommonModel",
                    "Equipment",
                ]
            }
        },
    )
    endDate: Optional[datetime] = Field(
        default=None, json_schema_extra={"linkml_meta": {"domain_of": ["Activity"]}}
    )
    identifier: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    name: str = Field(
        default=...,
        title="Name of project",
        description="""The name of the project that generated this Dandiset or asset.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    startDate: Optional[datetime] = Field(
        default=None, json_schema_extra={"linkml_meta": {"domain_of": ["Activity"]}}
    )
    used: Optional[list[Equipment]] = Field(
        default=None,
        description="""A listing of equipment used for the activity.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Activity"]}},
    )
    wasAssociatedWith: Optional[list[Union[Agent, Organization, Person, Software]]] = (
        Field(
            default=None,
            json_schema_extra={
                "linkml_meta": {
                    "any_of": [
                        {
                            "notes": [
                                "pydantic2linkml: Unable to translate the logic "
                                "contained in the after validation function, <function "
                                "Contributor.ensure_contact_person_has_email at "
                                "0xADDRESS>."
                            ],
                            "range": "Person",
                        },
                        {
                            "notes": [
                                "pydantic2linkml: Unable to translate the logic "
                                "contained in the after validation function, <function "
                                "Contributor.ensure_contact_person_has_email at "
                                "0xADDRESS>."
                            ],
                            "range": "Organization",
                        },
                        {"range": "Software"},
                        {"range": "Agent"},
                    ],
                    "domain_of": ["Activity"],
                }
            },
        )
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Project"] = Field(
        default="Project",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class PropertyValue(DandiBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7"}
    )

    maxValue: Optional[float] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["PropertyValue"],
                "notes": [
                    "pydantic2linkml: LinkML does not have support for `'+inf'`, "
                    "`'-inf'`, and `'NaN'` values. Support for these values is not "
                    "translated."
                ],
            }
        },
    )
    minValue: Optional[float] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["PropertyValue"],
                "notes": [
                    "pydantic2linkml: LinkML does not have support for `'+inf'`, "
                    "`'-inf'`, and `'NaN'` values. Support for these values is not "
                    "translated."
                ],
            }
        },
    )
    propertyID: Optional[Union[IdentifierType, str]] = Field(
        default=None,
        description="""A commonly used identifier for the characteristic represented by the property. For example, a known prefix like DOI or a full URL.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {"range": "IdentifierType"},
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                ],
                "domain_of": ["PropertyValue"],
            }
        },
    )
    unitText: Optional[str] = Field(
        default=None,
        json_schema_extra={"linkml_meta": {"domain_of": ["PropertyValue"]}},
    )
    value: Optional[Any] = Field(
        default=None,
        description="""The value associated with this property.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [{"range": "Any"}, {"multivalued": True, "range": "Any"}],
                "domain_of": ["PropertyValue"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <bound method "
                    "PropertyValue.ensure_value of <class "
                    "'dandischema.models.PropertyValue'>>."
                ],
            }
        },
    )
    valueReference: Optional[PropertyValue] = Field(
        default=None,
        json_schema_extra={"linkml_meta": {"domain_of": ["PropertyValue"]}},
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["PropertyValue"] = Field(
        default="PropertyValue",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class Publishable(DandiBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7"}
    )

    datePublished: datetime = Field(
        default=..., json_schema_extra={"linkml_meta": {"domain_of": ["Publishable"]}}
    )
    publishedBy: Union[PublishActivity, str] = Field(
        default=...,
        description="""The URL should contain the provenance of the publishing process.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {"range": "PublishActivity"},
                ],
                "domain_of": ["Publishable"],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Publishable"] = Field(
        default="Publishable",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class PublishActivity(Activity):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7"}
    )

    description: Optional[str] = Field(
        default=None,
        description="""The description of the activity.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "AccessRequirements",
                    "Activity",
                    "CommonModel",
                    "Equipment",
                ]
            }
        },
    )
    endDate: Optional[datetime] = Field(
        default=None, json_schema_extra={"linkml_meta": {"domain_of": ["Activity"]}}
    )
    identifier: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    name: str = Field(
        default=...,
        title="Title",
        description="""The name of the activity.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    startDate: Optional[datetime] = Field(
        default=None, json_schema_extra={"linkml_meta": {"domain_of": ["Activity"]}}
    )
    used: Optional[list[Equipment]] = Field(
        default=None,
        description="""A listing of equipment used for the activity.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Activity"]}},
    )
    wasAssociatedWith: Optional[list[Union[Agent, Organization, Person, Software]]] = (
        Field(
            default=None,
            json_schema_extra={
                "linkml_meta": {
                    "any_of": [
                        {
                            "notes": [
                                "pydantic2linkml: Unable to translate the logic "
                                "contained in the after validation function, <function "
                                "Contributor.ensure_contact_person_has_email at "
                                "0xADDRESS>."
                            ],
                            "range": "Person",
                        },
                        {
                            "notes": [
                                "pydantic2linkml: Unable to translate the logic "
                                "contained in the after validation function, <function "
                                "Contributor.ensure_contact_person_has_email at "
                                "0xADDRESS>."
                            ],
                            "range": "Organization",
                        },
                        {"range": "Software"},
                        {"range": "Agent"},
                    ],
                    "domain_of": ["Activity"],
                }
            },
        )
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["PublishActivity"] = Field(
        default="PublishActivity",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class PublishedAsset(Publishable, Asset):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "mixins": ["Publishable"],
            "notes": [
                "pydantic2linkml: Warning: LinkML does not support multiple "
                "inheritance. Publishable is not specified as a parent, through the "
                "`is_a` meta slot, but as a mixin.",
                "MANUAL_NOTE: The default of the `schemaKey` field in the "
                "corresponding Pydantic model in `dandischema.models` is not the "
                "model's name. Adjustment to the inherited `schemaKey` slot may be "
                "needed.",
            ],
            "slot_usage": {
                "id": {
                    "name": "id",
                    "pattern": "^dandiasset:[a-f0-9]{8}[-]*[a-f0-9]{4}[-]*[a-f0-9]{4}[-]*[a-f0-9]{4}[-]*[a-f0-9]{12}$",
                }
            },
        }
    )

    datePublished: datetime = Field(
        default=..., json_schema_extra={"linkml_meta": {"domain_of": ["Publishable"]}}
    )
    publishedBy: Union[PublishActivity, str] = Field(
        default=...,
        description="""The URL should contain the provenance of the publishing process.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {"range": "PublishActivity"},
                ],
                "domain_of": ["Publishable"],
            }
        },
    )
    contentUrl: list[str] = Field(
        default=...,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["Asset"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    identifier: str = Field(
        default=...,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    approach: Optional[list[ApproachType]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["AssetsSummary", "BareAsset"]}
        },
    )
    blobDateModified: Optional[datetime] = Field(
        default=None,
        title="Asset file modification date and time.",
        json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset"]}},
    )
    contentSize: Union[int, str] = Field(
        default=...,
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {"pattern": "^\\s*(\\d*\\.?\\d+)\\s*(\\w+)?", "range": "string"},
                    {"minimum_value": 0, "range": "integer"},
                ],
                "domain_of": ["BareAsset"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <bound method ByteSize._validate of "
                    "<class 'pydantic.types.ByteSize'>>."
                ],
            }
        },
    )
    dataType: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BareAsset"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    dateModified: Optional[datetime] = Field(
        default=None,
        title="Asset (file or metadata) modification date and time",
        json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset", "Dandiset"]}},
    )
    digest: str = Field(
        default=...,
        title="A map of dandi digests to their values",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BareAsset"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <bound method BareAsset.digest_check of "
                    "<class 'dandischema.models.BareAsset'>>.",
                    "pydantic2linkml: Warning: The translation is incomplete. `dict` "
                    "types are yet to be supported.",
                ],
            }
        },
    )
    encodingFormat: str = Field(
        default=...,
        title="File encoding format",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {"range": "string"},
                ],
                "domain_of": ["BareAsset"],
            }
        },
    )
    measurementTechnique: Optional[list[MeasurementTechniqueType]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["AssetsSummary", "BareAsset"]}
        },
    )
    path: str = Field(
        default=..., json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset"]}}
    )
    sameAs: Optional[list[str]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BareAsset", "BioSample", "Dandiset", "Participant"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    variableMeasured: Optional[list[PropertyValue]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["AssetsSummary", "BareAsset"]}
        },
    )
    wasAttributedTo: Optional[list[Participant]] = Field(
        default=None,
        description="""Associated participant(s) or subject(s).""",
        json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset", "BioSample"]}},
    )
    wasDerivedFrom: Optional[list[BioSample]] = Field(
        default=None,
        json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset", "BioSample"]}},
    )
    about: Optional[list[Union[Anatomy, Disorder, GenericType]]] = Field(
        default=None,
        title="Subject matter of the dataset",
        description="""The subject matter of the content, such as disorders, brain anatomy.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {"range": "Disorder"},
                    {"range": "Anatomy"},
                    {"range": "GenericType"},
                ],
                "domain_of": ["CommonModel"],
            }
        },
    )
    access: Optional[list[AccessRequirements]] = Field(
        default=None,
        title="Access information",
        max_length=1,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to express the default factory, <function "
                    "BareAsset.<lambda> at 0xADDRESS>, in LinkML.",
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <function "
                    "AccessRequirements.open_or_embargoed at 0xADDRESS>.",
                ],
            }
        },
    )
    acknowledgement: Optional[str] = Field(
        default=None,
        description="""Any acknowledgments not covered by contributors or external resources.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    contributor: Optional[list[Union[Organization, Person]]] = Field(
        default=None,
        title="Contributors",
        description="""Contributors to this item: persons or organizations.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the after validation function, <function "
                            "Contributor.ensure_contact_person_has_email at "
                            "0xADDRESS>."
                        ],
                        "range": "Person",
                    },
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the after validation function, <function "
                            "Contributor.ensure_contact_person_has_email at "
                            "0xADDRESS>."
                        ],
                        "range": "Organization",
                    },
                ],
                "domain_of": ["CommonModel"],
            }
        },
    )
    description: Optional[str] = Field(
        default=None,
        description="""A description of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "AccessRequirements",
                    "Activity",
                    "CommonModel",
                    "Equipment",
                ]
            }
        },
    )
    ethicsApproval: Optional[list[EthicsApproval]] = Field(
        default=None,
        title="Ethics approvals",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    keywords: Optional[list[str]] = Field(
        default=None,
        description="""Keywords used to describe this content.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    license: Optional[list[LicenseType]] = Field(
        default=None,
        description="""Licenses associated with the item. DANDI only supports a subset of Creative Commons Licenses (creativecommons.org) applicable to datasets.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    name: Optional[str] = Field(
        default=None,
        title="Title",
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    protocol: Optional[list[str]] = Field(
        default=None,
        description="""A list of persistent URLs describing the protocol (e.g. protocols.io, or other DOIs).""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    relatedResource: Optional[list[Resource]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <function Resource.identifier_or_url at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    repository: Optional[str] = Field(
        default=None,
        description="""location of the item""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel", "Resource"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    schemaVersion: Optional[str] = Field(
        default="0.7.0",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["CommonModel"], "ifabsent": "string(0.7.0)"}
        },
    )
    studyTarget: Optional[list[str]] = Field(
        default=None,
        description="""Objectives or specific questions of the study.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    url: Optional[str] = Field(
        default=None,
        description="""permalink to the item""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Agent",
                    "CommonModel",
                    "ContactPoint",
                    "Contributor",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    wasGeneratedBy: Optional[
        list[Union[Activity, Project, PublishActivity, Session]]
    ] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["CommonModel", "GenotypeInfo"]}
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["PublishedAsset"] = Field(
        default="PublishedAsset",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )

    @field_validator("contentUrl")
    def pattern_contentUrl(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid contentUrl format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid contentUrl format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("identifier")
    def pattern_identifier(cls, v):
        pattern = re.compile(
            r"^(?:urn:uuid:)?[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?4[0-9a-fA-F]{3}-?[89abAB][0-9a-fA-F]{3}-?[0-9a-fA-F]{12}$"
        )
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid identifier format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid identifier format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("dataType")
    def pattern_dataType(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid dataType format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid dataType format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("sameAs")
    def pattern_sameAs(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid sameAs format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid sameAs format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("protocol")
    def pattern_protocol(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid protocol format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid protocol format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("repository")
    def pattern_repository(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid repository format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid repository format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("url")
    def pattern_url(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid url format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid url format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("id")
    def pattern_id(cls, v):
        pattern = re.compile(
            r"^dandiasset:[a-f0-9]{8}[-]*[a-f0-9]{4}[-]*[a-f0-9]{4}[-]*[a-f0-9]{4}[-]*[a-f0-9]{12}$"
        )
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid id format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid id format: {v}"
            raise ValueError(err_msg)
        return v


class PublishedDandiset(Publishable, Dandiset):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "mixins": ["Publishable"],
            "notes": [
                "pydantic2linkml: Impossible to generate slot usage entry for the "
                "id slot. The slot representation of the id field in the "
                "PublishedDandiset Pydantic model has changes in value in "
                "constraint meta slots: ['pattern'] .",
                "pydantic2linkml: Impossible to generate slot usage entry for the "
                "url slot. The slot representation of the url field in the "
                "PublishedDandiset Pydantic model has changes in value in "
                "constraint meta slots: ['required'] .",
                "pydantic2linkml: Warning: LinkML does not support multiple "
                "inheritance. Publishable is not specified as a parent, through the "
                "`is_a` meta slot, but as a mixin.",
                "MANUAL_NOTE: The default of the `schemaKey` field in the "
                "corresponding Pydantic model in `dandischema.models` is not the "
                "model's name. Adjustment to the inherited `schemaKey` slot may be "
                "needed.",
            ],
        }
    )

    doi: Optional[str] = Field(
        default="",
        title="DOI",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["PublishedDandiset"], "ifabsent": "string()"}
        },
    )
    releaseNotes: Optional[str] = Field(
        default=None,
        description="""The description of the release""",
        json_schema_extra={"linkml_meta": {"domain_of": ["PublishedDandiset"]}},
    )
    datePublished: datetime = Field(
        default=..., json_schema_extra={"linkml_meta": {"domain_of": ["Publishable"]}}
    )
    publishedBy: Union[PublishActivity, str] = Field(
        default=...,
        description="""The URL should contain the provenance of the publishing process.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {"range": "PublishActivity"},
                ],
                "domain_of": ["Publishable"],
            }
        },
    )
    assetsSummary: AssetsSummary = Field(
        default=..., json_schema_extra={"linkml_meta": {"domain_of": ["Dandiset"]}}
    )
    citation: str = Field(
        default=..., json_schema_extra={"linkml_meta": {"domain_of": ["Dandiset"]}}
    )
    dateCreated: Optional[datetime] = Field(
        default=None,
        title="Dandiset creation date and time.",
        json_schema_extra={"linkml_meta": {"domain_of": ["Dandiset"]}},
    )
    dateModified: Optional[datetime] = Field(
        default=None,
        title="Last modification date and time.",
        json_schema_extra={"linkml_meta": {"domain_of": ["BareAsset", "Dandiset"]}},
    )
    identifier: str = Field(
        default=...,
        title="Dandiset identifier",
        description="""A Dandiset identifier that can be resolved by identifiers.org.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    manifestLocation: list[str] = Field(
        default=...,
        min_length=1,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["Dandiset"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    sameAs: Optional[list[str]] = Field(
        default=None,
        description="""Known DANDI URLs of the Dandiset at other DANDI instances.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BareAsset", "BioSample", "Dandiset", "Participant"]
            }
        },
    )
    version: str = Field(
        default=...,
        json_schema_extra={"linkml_meta": {"domain_of": ["Dandiset", "Software"]}},
    )
    about: Optional[list[Union[Anatomy, Disorder, GenericType]]] = Field(
        default=None,
        title="Subject matter of the dataset",
        description="""The subject matter of the content, such as disorders, brain anatomy.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {"range": "Disorder"},
                    {"range": "Anatomy"},
                    {"range": "GenericType"},
                ],
                "domain_of": ["CommonModel"],
            }
        },
    )
    access: Optional[list[AccessRequirements]] = Field(
        default=None,
        title="Access information",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to express the default factory, <function "
                    "CommonModel.<lambda> at 0xADDRESS>, in LinkML.",
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <function "
                    "AccessRequirements.open_or_embargoed at 0xADDRESS>.",
                ],
            }
        },
    )
    acknowledgement: Optional[str] = Field(
        default=None,
        description="""Any acknowledgments not covered by contributors or external resources.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    contributor: Optional[list[Union[Organization, Person]]] = Field(
        default=None,
        title="Contributors",
        description="""Contributors to this item: persons or organizations.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the after validation function, <function "
                            "Contributor.ensure_contact_person_has_email at "
                            "0xADDRESS>."
                        ],
                        "range": "Person",
                    },
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the after validation function, <function "
                            "Contributor.ensure_contact_person_has_email at "
                            "0xADDRESS>."
                        ],
                        "range": "Organization",
                    },
                ],
                "domain_of": ["CommonModel"],
            }
        },
    )
    description: Optional[str] = Field(
        default=None,
        description="""A description of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "AccessRequirements",
                    "Activity",
                    "CommonModel",
                    "Equipment",
                ]
            }
        },
    )
    ethicsApproval: Optional[list[EthicsApproval]] = Field(
        default=None,
        title="Ethics approvals",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    keywords: Optional[list[str]] = Field(
        default=None,
        description="""Keywords used to describe this content.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    license: Optional[list[LicenseType]] = Field(
        default=None,
        description="""Licenses associated with the item. DANDI only supports a subset of Creative Commons Licenses (creativecommons.org) applicable to datasets.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    name: Optional[str] = Field(
        default=None,
        title="Title",
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    protocol: Optional[list[str]] = Field(
        default=None,
        description="""A list of persistent URLs describing the protocol (e.g. protocols.io, or other DOIs).""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    relatedResource: Optional[list[Resource]] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "after validation function, <function Resource.identifier_or_url at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    repository: Optional[str] = Field(
        default=None,
        description="""location of the item""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["CommonModel", "Resource"],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    schemaVersion: Optional[str] = Field(
        default="0.7.0",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["CommonModel"], "ifabsent": "string(0.7.0)"}
        },
    )
    studyTarget: Optional[list[str]] = Field(
        default=None,
        description="""Objectives or specific questions of the study.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}},
    )
    url: Optional[str] = Field(
        default=None,
        description="""permalink to the item""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Agent",
                    "CommonModel",
                    "ContactPoint",
                    "Contributor",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    wasGeneratedBy: Optional[
        list[Union[Activity, Project, PublishActivity, Session]]
    ] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {"domain_of": ["CommonModel", "GenotypeInfo"]}
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["PublishedDandiset"] = Field(
        default="PublishedDandiset",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )

    @field_validator("doi")
    def pattern_doi(cls, v):
        pattern = re.compile(r"^(10\.\d{4,}/[a-z][-a-z]*\.\d{6}/\d+\.\d+\.\d+|)$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid doi format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid doi format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("identifier")
    def pattern_identifier(cls, v):
        pattern = re.compile(r"^[A-Z][-A-Z]*:\d{6}$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid identifier format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid identifier format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("manifestLocation")
    def pattern_manifestLocation(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid manifestLocation format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid manifestLocation format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("sameAs")
    def pattern_sameAs(cls, v):
        pattern = re.compile(
            r"^dandi://[A-Z][-A-Z]*/\d{6}(@(draft|\d+\.\d+\.\d+))?(/\S+)?$"
        )
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid sameAs format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid sameAs format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("protocol")
    def pattern_protocol(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid protocol format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid protocol format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("repository")
    def pattern_repository(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid repository format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid repository format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("url")
    def pattern_url(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid url format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid url format: {v}"
            raise ValueError(err_msg)
        return v


class RelatedParticipant(DandiBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "identifier": {
                    "name": "identifier",
                    "range": "string",
                    "required": False,
                },
                "name": {
                    "name": "name",
                    "required": False,
                    "title": "Name of the participant or subject",
                },
                "relation": {
                    "description": "Indicates how the current "
                    "participant or subject is related "
                    "to the other participant or "
                    "subject. This relation should "
                    "satisfy: Participant/Subject "
                    "<relation> "
                    "relatedParticipant/Subject.",
                    "name": "relation",
                    "range": "ParticipantRelationType",
                    "title": "Participant or subject relation",
                },
                "url": {
                    "name": "url",
                    "notes": [
                        "pydantic2linkml: Unable to translate the "
                        "logic contained in the wrap validation "
                        "function, <function "
                        "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                        "at 0xADDRESS>."
                    ],
                    "required": False,
                    "title": "URL of the related participant or subject",
                },
            },
        }
    )

    identifier: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    name: Optional[str] = Field(
        default=None,
        title="Name of the participant or subject",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    relation: ParticipantRelationType = Field(
        default=...,
        title="Participant or subject relation",
        description="""Indicates how the current participant or subject is related to the other participant or subject. This relation should satisfy: Participant/Subject <relation> relatedParticipant/Subject.""",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["RelatedParticipant", "Resource"]}
        },
    )
    url: Optional[str] = Field(
        default=None,
        title="URL of the related participant or subject",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Agent",
                    "CommonModel",
                    "ContactPoint",
                    "Contributor",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["RelatedParticipant"] = Field(
        default="RelatedParticipant",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )

    @field_validator("url")
    def pattern_url(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid url format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid url format: {v}"
            raise ValueError(err_msg)
        return v


class Resource(DandiBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "identifier": {
                    "name": "identifier",
                    "range": "string",
                    "required": False,
                },
                "name": {
                    "name": "name",
                    "required": False,
                    "title": "A title of the resource",
                },
                "relation": {
                    "description": "Indicates how the resource is "
                    "related to the dataset. This "
                    "relation should satisfy: dandiset "
                    "<relation> resource.",
                    "name": "relation",
                    "range": "RelationType",
                    "title": "Resource relation",
                },
                "repository": {
                    "description": "Name of the repository in which "
                    "the resource is housed.",
                    "name": "repository",
                    "range": "string",
                    "title": "Name of the repository",
                },
                "url": {
                    "name": "url",
                    "notes": [
                        "pydantic2linkml: Unable to translate the "
                        "logic contained in the wrap validation "
                        "function, <function "
                        "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                        "at 0xADDRESS>."
                    ],
                    "required": False,
                    "title": "URL of the resource",
                },
            },
        }
    )

    identifier: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    name: Optional[str] = Field(
        default=None,
        title="A title of the resource",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    relation: RelationType = Field(
        default=...,
        title="Resource relation",
        description="""Indicates how the resource is related to the dataset. This relation should satisfy: dandiset <relation> resource.""",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["RelatedParticipant", "Resource"]}
        },
    )
    repository: Optional[str] = Field(
        default=None,
        title="Name of the repository",
        description="""Name of the repository in which the resource is housed.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel", "Resource"]}},
    )
    resourceType: Optional[ResourceType] = Field(
        default=None,
        title="Resource type",
        description="""The type of resource.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Resource"]}},
    )
    url: Optional[str] = Field(
        default=None,
        title="URL of the resource",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Agent",
                    "CommonModel",
                    "ContactPoint",
                    "Contributor",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Resource"] = Field(
        default="Resource",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )

    @field_validator("url")
    def pattern_url(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid url format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid url format: {v}"
            raise ValueError(err_msg)
        return v


class SampleType(BaseType):
    """
    OBI based identifier for the sample type used
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7"}
    )

    identifier: Optional[str] = Field(
        default=None,
        description="""The identifier can be any url or a compact URI, preferably supported by identifiers.org.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {
                        "pattern": "^[a-zA-Z0-9-]+:[a-zA-Z0-9-/\\._]+$",
                        "range": "string",
                    },
                ],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    name: Optional[str] = Field(
        default=None,
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["SampleType"] = Field(
        default="SampleType",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class Session(Activity):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "description": {
                    "description": "A brief description of the " "session.",
                    "name": "description",
                },
                "name": {
                    "description": "The name of the logical session "
                    "associated with the asset.",
                    "name": "name",
                    "title": "Name of session",
                },
            },
        }
    )

    description: Optional[str] = Field(
        default=None,
        description="""A brief description of the session.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "AccessRequirements",
                    "Activity",
                    "CommonModel",
                    "Equipment",
                ]
            }
        },
    )
    endDate: Optional[datetime] = Field(
        default=None, json_schema_extra={"linkml_meta": {"domain_of": ["Activity"]}}
    )
    identifier: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    name: str = Field(
        default=...,
        title="Name of session",
        description="""The name of the logical session associated with the asset.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    startDate: Optional[datetime] = Field(
        default=None, json_schema_extra={"linkml_meta": {"domain_of": ["Activity"]}}
    )
    used: Optional[list[Equipment]] = Field(
        default=None,
        description="""A listing of equipment used for the activity.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["Activity"]}},
    )
    wasAssociatedWith: Optional[list[Union[Agent, Organization, Person, Software]]] = (
        Field(
            default=None,
            json_schema_extra={
                "linkml_meta": {
                    "any_of": [
                        {
                            "notes": [
                                "pydantic2linkml: Unable to translate the logic "
                                "contained in the after validation function, <function "
                                "Contributor.ensure_contact_person_has_email at "
                                "0xADDRESS>."
                            ],
                            "range": "Person",
                        },
                        {
                            "notes": [
                                "pydantic2linkml: Unable to translate the logic "
                                "contained in the after validation function, <function "
                                "Contributor.ensure_contact_person_has_email at "
                                "0xADDRESS>."
                            ],
                            "range": "Organization",
                        },
                        {"range": "Software"},
                        {"range": "Agent"},
                    ],
                    "domain_of": ["Activity"],
                }
            },
        )
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Session"] = Field(
        default="Session",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class SexType(BaseType):
    """
    Identifier for the sex of the sample
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7"}
    )

    identifier: Optional[str] = Field(
        default=None,
        description="""The identifier can be any url or a compact URI, preferably supported by identifiers.org.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {
                        "pattern": "^[a-zA-Z0-9-]+:[a-zA-Z0-9-/\\._]+$",
                        "range": "string",
                    },
                ],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    name: Optional[str] = Field(
        default=None,
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["SexType"] = Field(
        default="SexType",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class Software(DandiBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7",
            "slot_usage": {
                "identifier": {
                    "description": "RRID of the software from " "scicrunch.org.",
                    "name": "identifier",
                    "pattern": "^RRID:.*",
                    "range": "string",
                    "required": False,
                    "title": "Research resource identifier",
                },
                "name": {"name": "name", "required": True},
                "url": {
                    "description": "Web page for the software.",
                    "name": "url",
                    "notes": [
                        "pydantic2linkml: Unable to translate the "
                        "logic contained in the wrap validation "
                        "function, <function "
                        "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                        "at 0xADDRESS>."
                    ],
                    "required": False,
                },
            },
        }
    )

    identifier: Optional[str] = Field(
        default=None,
        title="Research resource identifier",
        description="""RRID of the software from scicrunch.org.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    name: str = Field(
        default=...,
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ]
            }
        },
    )
    url: Optional[str] = Field(
        default=None,
        description="""Web page for the software.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": [
                    "Agent",
                    "CommonModel",
                    "ContactPoint",
                    "Contributor",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
                "notes": [
                    "pydantic2linkml: Unable to translate the logic contained in the "
                    "wrap validation function, <function "
                    "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val at "
                    "0xADDRESS>."
                ],
            }
        },
    )
    version: str = Field(
        default=...,
        json_schema_extra={"linkml_meta": {"domain_of": ["Dandiset", "Software"]}},
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["Software"] = Field(
        default="Software",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )

    @field_validator("identifier")
    def pattern_identifier(cls, v):
        pattern = re.compile(r"^RRID:.*")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid identifier format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid identifier format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator("url")
    def pattern_url(cls, v):
        pattern = re.compile(r"^(?i:http|https)://[^\s]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid url format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid url format: {v}"
            raise ValueError(err_msg)
        return v


class SpeciesType(BaseType):
    """
    Identifier for species of the sample
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7"}
    )

    identifier: Optional[str] = Field(
        default=None,
        description="""The identifier can be any url or a compact URI, preferably supported by identifiers.org.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {
                        "pattern": "^[a-zA-Z0-9-]+:[a-zA-Z0-9-/\\._]+$",
                        "range": "string",
                    },
                ],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    name: Optional[str] = Field(
        default=None,
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["SpeciesType"] = Field(
        default="SpeciesType",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class StandardsType(BaseType):
    """
    Identifier for data standard used
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7"}
    )

    identifier: Optional[str] = Field(
        default=None,
        description="""The identifier can be any url or a compact URI, preferably supported by identifiers.org.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {
                        "pattern": "^[a-zA-Z0-9-]+:[a-zA-Z0-9-/\\._]+$",
                        "range": "string",
                    },
                ],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    name: Optional[str] = Field(
        default=None,
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["StandardsType"] = Field(
        default="StandardsType",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


class StrainType(BaseType):
    """
    Identifier for the strain of the sample
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://schema.dandiarchive.org/s/dandi/v0.7"}
    )

    identifier: Optional[str] = Field(
        default=None,
        description="""The identifier can be any url or a compact URI, preferably supported by identifiers.org.""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [
                    {
                        "notes": [
                            "pydantic2linkml: Unable to translate the logic "
                            "contained in the wrap validation function, <function "
                            "_BaseUrl.__get_pydantic_core_schema__.<locals>.wrap_val "
                            "at 0xADDRESS>."
                        ],
                        "pattern": "^(?i:http|https)://[^\\s]+$",
                        "range": "uri",
                    },
                    {
                        "pattern": "^[a-zA-Z0-9-]+:[a-zA-Z0-9-/\\._]+$",
                        "range": "string",
                    },
                ],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "Allele",
                    "Asset",
                    "BaseType",
                    "BioSample",
                    "Contributor",
                    "Dandiset",
                    "Equipment",
                    "EthicsApproval",
                    "Locus",
                    "Participant",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    name: Optional[str] = Field(
        default=None,
        description="""The name of the item.""",
        json_schema_extra={
            "linkml_meta": {
                "all_of": [{"pattern": "^[\\s\\S]{,150}\\Z"}],
                "domain_of": [
                    "Activity",
                    "Affiliation",
                    "Agent",
                    "BaseType",
                    "CommonModel",
                    "Contributor",
                    "Equipment",
                    "RelatedParticipant",
                    "Resource",
                    "Software",
                ],
            }
        },
    )
    id: Optional[str] = Field(
        default=None,
        description="""Uniform resource identifier""",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"]}},
    )
    schemaKey: Literal["StrainType"] = Field(
        default="StrainType",
        json_schema_extra={
            "linkml_meta": {"designates_type": True, "domain_of": ["DandiBaseModel"]}
        },
    )


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
DandiBaseModel.model_rebuild()
AccessRequirements.model_rebuild()
Activity.model_rebuild()
Affiliation.model_rebuild()
Agent.model_rebuild()
Allele.model_rebuild()
AssetsSummary.model_rebuild()
BaseType.model_rebuild()
Anatomy.model_rebuild()
ApproachType.model_rebuild()
AssayType.model_rebuild()
BioSample.model_rebuild()
CommonModel.model_rebuild()
BareAsset.model_rebuild()
Asset.model_rebuild()
ContactPoint.model_rebuild()
Contributor.model_rebuild()
Dandiset.model_rebuild()
Disorder.model_rebuild()
Equipment.model_rebuild()
EthicsApproval.model_rebuild()
GenericType.model_rebuild()
GenotypeInfo.model_rebuild()
Locus.model_rebuild()
MeasurementTechniqueType.model_rebuild()
Organization.model_rebuild()
Participant.model_rebuild()
Person.model_rebuild()
Project.model_rebuild()
PropertyValue.model_rebuild()
Publishable.model_rebuild()
PublishActivity.model_rebuild()
PublishedAsset.model_rebuild()
PublishedDandiset.model_rebuild()
RelatedParticipant.model_rebuild()
Resource.model_rebuild()
SampleType.model_rebuild()
Session.model_rebuild()
SexType.model_rebuild()
Software.model_rebuild()
SpeciesType.model_rebuild()
StandardsType.model_rebuild()
StrainType.model_rebuild()
