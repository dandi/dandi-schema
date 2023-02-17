from copy import deepcopy
from datetime import date, datetime
from enum import Enum
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast

from pydantic import (
    UUID4,
    AnyHttpUrl,
    BaseModel,
    ByteSize,
    EmailStr,
    Field,
    parse_obj_as,
    root_validator,
    validator,
)

from .consts import DANDI_SCHEMA_VERSION
from .digests.dandietag import DandiETag
from .digests.zarr import ZARR_CHECKSUM_PATTERN, parse_directory_digest
from .utils import name2title

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

# Use DJANGO_DANDI_WEB_APP_URL to point to a specific deployment.
try:
    DANDI_INSTANCE_URL = os.environ["DJANGO_DANDI_WEB_APP_URL"]
except KeyError:
    DANDI_INSTANCE_URL = "http://localhost/"
    DANDI_INSTANCE_URL_PATTERN = ".*"
else:
    # Ensure no trailing / for consistency
    DANDI_INSTANCE_URL_PATTERN = re.escape(DANDI_INSTANCE_URL.rstrip("/"))

NAME_PATTERN = r"^([\w\s\-\.']+),\s+([\w\s\-\.']+)$"
UUID_PATTERN = (
    "[a-f0-9]{8}[-]*[a-f0-9]{4}[-]*" "[a-f0-9]{4}[-]*[a-f0-9]{4}[-]*[a-f0-9]{12}$"
)
ASSET_UUID_PATTERN = r"^dandiasset:" + UUID_PATTERN
VERSION_PATTERN = r"\d{6}/\d+\.\d+\.\d+"
DANDI_DOI_PATTERN = rf"^10.(48324|80507)/dandi\.{VERSION_PATTERN}"
DANDI_PUBID_PATTERN = rf"^DANDI:{VERSION_PATTERN}"
PUBLISHED_VERSION_URL_PATTERN = (
    rf"^{DANDI_INSTANCE_URL_PATTERN}/dandiset/{VERSION_PATTERN}$"
)
MD5_PATTERN = r"[0-9a-f]{32}"
SHA256_PATTERN = r"[0-9a-f]{64}"


M = TypeVar("M", bound=BaseModel)


def diff_models(model1: M, model2: M) -> None:
    """Perform a field-wise diff"""
    for field in model1.__fields__:
        if getattr(model1, field) != getattr(model2, field):
            print(f"{field} is different")


def _sanitize(o: Any) -> Any:
    if isinstance(o, dict):
        return {_sanitize(k): _sanitize(v) for k, v in o.items()}
    elif isinstance(o, (set, tuple, list)):
        return type(o)(_sanitize(x) for x in o)
    elif isinstance(o, Enum):
        return o.value
    return o


class AccessType(Enum):
    """An enumeration of access status options"""

    #: The dandiset is openly accessible
    OpenAccess = "dandi:OpenAccess"

    #: The dandiset is embargoed
    EmbargoedAccess = "dandi:EmbargoedAccess"

    """
    Uncomment when restricted access is implemented:
        #: The dandiset is restricted
        RestrictedAccess = "dandi:RestrictedAccess"
    """


class DigestType(Enum):
    """An enumeration of checksum types"""

    #: MD5 checksum
    md5 = "dandi:md5"

    #: SHA1 checksum
    sha1 = "dandi:sha1"

    #: SHA2-256 checksum
    sha2_256 = "dandi:sha2-256"

    #: SHA3-256 checksum
    sha3_256 = "dandi:sha3-256"

    #: BLAKE2B-256 checksum
    blake2b_256 = "dandi:blake2b-256"

    #: BLAKE3-256 checksum
    blake3 = "dandi:blake3"

    #: S3-style ETag
    dandi_etag = "dandi:dandi-etag"

    #: DANDI Zarr checksum
    dandi_zarr_checksum = "dandi:dandi-zarr-checksum"


class IdentifierType(Enum):
    """An enumeration of identifiers"""

    doi = "dandi:doi"
    orcid = "dandi:orcid"
    ror = "dandi:ror"
    dandi = "dandi:dandi"
    rrid = "dandi:rrid"


class LicenseType(Enum):
    """An enumeration of supported licenses"""

    CC0_10 = "spdx:CC0-1.0"
    CC_BY_40 = "spdx:CC-BY-4.0"


class RelationType(Enum):
    """An enumeration of resource relations"""

    #: Indicates that B includes A in a citation
    IsCitedBy = "dcite:IsCitedBy"

    #: Indicates that A includes B in a citation
    Cites = "dcite:Cites"

    #: Indicates that A is a supplement to B
    IsSupplementTo = "dcite:IsSupplementTo"

    #: Indicates that B is a supplement to A
    IsSupplementedBy = "dcite:IsSupplementedBy"

    #: Indicates A is continued by the work B
    IsContinuedBy = "dcite:IsContinuedBy"

    #: Indicates A is a continuation of the work B
    Continues = "dcite:Continues"

    #: Indicates A describes B
    Describes = "dcite:Describes"

    #: Indicates A is described by B
    IsDescribedBy = "dcite:IsDescribedBy"

    #: Indicates resource A has additional metadata B
    HasMetadata = "dcite:HasMetadata"

    #: Indicates additional metadata A for a resource B
    IsMetadataFor = "dcite:IsMetadataFor"

    #: Indicates A has a version (B)
    HasVersion = "dcite:HasVersion"

    #: Indicates A is a version of B
    IsVersionOf = "dcite:IsVersionOf"

    #: Indicates A is a new edition of B
    IsNewVersionOf = "dcite:IsNewVersionOf"

    #: Indicates A is a previous edition of B
    IsPreviousVersionOf = "dcite:IsPreviousVersionOf"

    #: Indicates A is a portion of B
    IsPartOf = "dcite:IsPartOf"

    #: Indicates A includes the part B
    HasPart = "dcite:HasPart"

    #: Indicates A is used as a source of information by B
    IsReferencedBy = "dcite:IsReferencedBy"

    #: Indicates B is used as a source of information for A
    References = "dcite:References"

    #: Indicates B is documentation about/explaining A
    IsDocumentedBy = "dcite:IsDocumentedBy"

    #: Indicates A is documentation about B
    Documents = "dcite:Documents"

    #: Indicates B is used to compile or create A
    IsCompiledBy = "dcite:IsCompiledBy"

    #: Indicates B is the result of a compile or creation event using A
    Compiles = "dcite:Compiles"

    #: Indicates A is a variant or different form of B
    IsVariantFormOf = "dcite:IsVariantFormOf"

    #: Indicates A is the original form of B
    IsOriginalFormOf = "dcite:IsOriginalFormOf"

    #: Indicates that A is identical to B
    IsIdenticalTo = "dcite:IsIdenticalTo"

    #: Indicates that A is reviewed by B
    IsReviewedBy = "dcite:IsReviewedBy"

    #: Indicates that A is a review of B
    Reviews = "dcite:Reviews"

    #: Indicates B is a source upon which A is based
    IsDerivedFrom = "dcite:IsDerivedFrom"

    #: Indicates A is a source upon which B is based
    IsSourceOf = "dcite:IsSourceOf"

    #: Indicates A is required by B
    IsRequiredBy = "dcite:IsRequiredBy"

    #: Indicates A requires B
    Requires = "dcite:Requires"

    #: Indicates A replaces B
    Obsoletes = "dcite:Obsoletes"

    #: Indicates A is replaced by B
    IsObsoletedBy = "dcite:IsObsoletedBy"

    #: Indicates A is published in B
    IsPublishedIn = "dcite:IsPublishedIn"


class ParticipantRelationType(Enum):
    """An enumeration of participant relations"""

    #: Indicates that A is a child of B
    isChildOf = "dandi:isChildOf"

    #: Indicates that A is a parent of B
    isParentOf = "dandi:isParentOf"

    #: Indicates that A is a sibling of B
    isSiblingOf = "dandi:isSiblingOf"

    #: Indicates that A is a monozygotic twin of B
    isMonozygoticTwinOf = "dandi:isMonozygoticTwinOf"

    #: Indicates that A is a dizygotic twin of B
    isDizygoticTwinOf = "dandi:isDizygoticTwinOf"


class RoleType(Enum):
    """An enumeration of roles"""

    #: Author
    Author = "dcite:Author"

    #: Conceptualization
    Conceptualization = "dcite:Conceptualization"

    #: Contact Person
    ContactPerson = "dcite:ContactPerson"

    #: Data Collector
    DataCollector = "dcite:DataCollector"

    #: Data Curator
    DataCurator = "dcite:DataCurator"

    #: Data Manager
    DataManager = "dcite:DataManager"

    #: Formal Analysis
    FormalAnalysis = "dcite:FormalAnalysis"

    #: Funding Acquisition
    FundingAcquisition = "dcite:FundingAcquisition"

    #: Investigation
    Investigation = "dcite:Investigation"

    #: Maintainer
    Maintainer = "dcite:Maintainer"

    #: Methodology
    Methodology = "dcite:Methodology"

    #: Producer
    Producer = "dcite:Producer"

    #: Project Leader
    ProjectLeader = "dcite:ProjectLeader"

    #: Project Manager
    ProjectManager = "dcite:ProjectManager"

    #: Project Member
    ProjectMember = "dcite:ProjectMember"

    #: Project Administration
    ProjectAdministration = "dcite:ProjectAdministration"

    #: Researcher
    Researcher = "dcite:Researcher"

    #: Resources
    Resources = "dcite:Resources"

    #: Software
    Software = "dcite:Software"

    #: Supervision
    Supervision = "dcite:Supervision"

    #: Validation
    Validation = "dcite:Validation"

    #: Visualization
    Visualization = "dcite:Visualization"

    #: Funder
    Funder = "dcite:Funder"

    #: Sponsor
    Sponsor = "dcite:Sponsor"

    #: Participant in a study
    StudyParticipant = "dcite:StudyParticipant"

    #: Affiliated with an entity
    Affiliation = "dcite:Affiliation"

    #: Approved ethics protocol
    EthicsApproval = "dcite:EthicsApproval"

    #: Other
    Other = "dcite:Other"


class AgeReferenceType(Enum):
    """An enumeration of age reference"""

    #: Age since Birth
    BirthReference = "dandi:BirthReference"

    #: Age of a pregnancy (https://en.wikipedia.org/wiki/Gestational_age)
    GestationalReference = "dandi:GestationalReference"


class HandleKeyEnumEncoder(json.JSONEncoder):
    def encode(self, o: Any) -> Any:
        return super().encode(_sanitize(o))


class DandiBaseModel(BaseModel):
    id: Optional[str] = Field(
        default=None, description="Uniform resource identifier", readOnly=True
    )
    schemaKey: Literal["DandiBaseModel"] = Field("DandiBaseModel", readOnly=True)

    def json_dict(self) -> dict:
        """
        Recursively convert the instance to a `dict` of JSONable values,
        including converting enum values to strings.  `None` fields
        are omitted.
        """
        return cast(
            dict, json.loads(self.json(exclude_none=True, cls=HandleKeyEnumEncoder))
        )

    @validator("schemaKey", always=True)
    @classmethod
    def ensure_schemakey(cls, val: str) -> str:
        tempval = val
        if "Published" in cls.__name__:
            tempval = "Published" + tempval
        elif "BareAsset" == cls.__name__:
            tempval = "Bare" + tempval
        if tempval != cls.__name__:
            raise ValueError(
                f"schemaKey {tempval} does not match classname {cls.__name__}"
            )
        return val

    @classmethod
    def unvalidated(__pydantic_cls__: Type[BaseModel], **data: Any) -> BaseModel:
        """Allow model to be returned without validation"""
        for name, field in __pydantic_cls__.__fields__.items():
            try:
                data[name]
            except KeyError:
                # if field.required:
                #    value = None
                if field.default_factory is not None:
                    value = field.default_factory()
                elif field.default is None:
                    # deepcopy is quite slow on None
                    value = None
                else:
                    value = deepcopy(field.default)
                data[name] = value
        return __pydantic_cls__.construct(**data)

    @classmethod
    def to_dictrepr(__pydantic_cls__: Type["DandiBaseModel"]) -> str:
        return (
            __pydantic_cls__.unvalidated()
            .__repr__()
            .replace(__pydantic_cls__.__name__, "dict")
        )

    class Config:
        @staticmethod
        def schema_extra(schema: Dict[str, Any], model: Type["BaseType"]) -> None:
            if schema["title"] == "PropertyValue":
                schema["required"] = sorted({"value"}.union(schema.get("required", [])))
            schema["title"] = name2title(schema["title"])
            if schema["type"] == "object":
                schema["required"] = sorted(
                    {"schemaKey"}.union(schema.get("required", []))
                )
            for prop, value in schema.get("properties", {}).items():
                if schema["title"] == "Person":
                    if prop == "name":
                        # JSON schema doesn't support validating unicode
                        # characters using the \w pattern, but Python does. So
                        # we are dropping the regex pattern for the schema.
                        del value["pattern"]
                if value.get("title") is None or value["title"] == prop.title():
                    value["title"] = name2title(prop)
                if re.match("\\^https?://", value.get("pattern", "")):
                    value["format"] = "uri"
                if value.get("format", None) == "uri":
                    value["maxLength"] = 1000
                allOf = value.get("allOf")
                anyOf = value.get("anyOf")
                items = value.get("items")
                if allOf is not None:
                    if len(allOf) == 1 and "$ref" in allOf[0]:
                        value["$ref"] = allOf[0]["$ref"]
                        del value["allOf"]
                    elif len(allOf) > 1:
                        value["oneOf"] = value["allOf"]
                        value["type"] = "object"
                        del value["allOf"]
                if anyOf is not None:
                    if len(anyOf) > 1 and any(["$ref" in val for val in anyOf]):
                        value["type"] = "object"
                if items is not None:
                    anyOf = items.get("anyOf")
                    if (
                        anyOf is not None
                        and len(anyOf) > 1
                        and any(["$ref" in val for val in anyOf])
                    ):
                        value["items"]["type"] = "object"
                # In pydantic 1.8+ all Literals are mapped on to enum
                # This presently breaks the schema editor UI. Revert
                # to const when generating the schema.
                # Note: this no longer happens with custom metaclass
                if prop == "schemaKey":
                    if "enum" in value and len(value["enum"]) == 1:
                        value["const"] = value["enum"][0]
                        del value["enum"]
                    else:
                        value["const"] = value["default"]
                    if "readOnly" in value:
                        del value["readOnly"]


class PropertyValue(DandiBaseModel):
    maxValue: Optional[float] = Field(None, nskey="schema")
    minValue: Optional[float] = Field(None, nskey="schema")
    unitText: Optional[str] = Field(None, nskey="schema")
    value: Union[Any, List[Any]] = Field(
        nskey="schema", description="The value associated with this property."
    )
    valueReference: Optional["PropertyValue"] = Field(
        None, nskey="schema"
    )  # Note: recursive (circular or not)
    propertyID: Optional[Union[IdentifierType, AnyHttpUrl]] = Field(
        None,
        description="A commonly used identifier for"
        "the characteristic represented by the property. "
        "For example, a known prefix like DOI or a full URL.",
        nskey="schema",
    )
    schemaKey: Literal["PropertyValue"] = Field("PropertyValue", readOnly=True)

    @validator("value", always=True)
    def ensure_value(cls, val: Union[Any, List[Any]]) -> Union[Any, List[Any]]:
        if not val:
            raise ValueError(
                "The value field of a PropertyValue cannot be None or empty."
            )
        return val

    _ldmeta = {"nskey": "schema"}


PropertyValue.update_forward_refs()

Identifier = str
ORCID = str
RORID = str
DANDI = str
RRID = str


class BaseType(DandiBaseModel):
    """Base class for enumerated types"""

    identifier: Optional[Union[AnyHttpUrl, str]] = Field(
        None,
        description="The identifier can be any url or a compact URI, preferably"
        " supported by identifiers.org.",
        regex=r"^[a-zA-Z0-9-]+:[a-zA-Z0-9-/\._]+$",
        nskey="schema",
    )
    name: Optional[str] = Field(
        None, description="The name of the item.", max_length=150, nskey="schema"
    )
    schemaKey: Literal["BaseType"] = Field("BaseType", readOnly=True)
    _ldmeta = {"rdfs:subClassOf": ["prov:Entity", "schema:Thing"], "nskey": "dandi"}

    class Config:
        @staticmethod
        def schema_extra(schema: Dict[str, Any], model: Type["BaseType"]) -> None:
            DandiBaseModel.Config.schema_extra(schema=schema, model=model)
            for prop, value in schema.get("properties", {}).items():
                # This check removes the anyOf field from the identifier property
                # in the schema generation. This relates to a UI issue where two
                # basic properties, in this case "string", is dropped from the UI.
                if prop == "identifier":
                    for option in value.pop("anyOf", []):
                        if option.get("format", "") == "uri":
                            value.update(**option)
                            value["maxLength"] = 1000


class AssayType(BaseType):
    """OBI based identifier for the assay(s) used"""

    schemaKey: Literal["AssayType"] = Field("AssayType", readOnly=True)


class SampleType(BaseType):
    """OBI based identifier for the sample type used"""

    schemaKey: Literal["SampleType"] = Field("SampleType", readOnly=True)


class Anatomy(BaseType):
    """UBERON or other identifier for anatomical part studied"""

    schemaKey: Literal["Anatomy"] = Field("Anatomy", readOnly=True)


class StrainType(BaseType):
    """Identifier for the strain of the sample"""

    schemaKey: Literal["StrainType"] = Field("StrainType", readOnly=True)


class SexType(BaseType):
    """Identifier for the sex of the sample"""

    schemaKey: Literal["SexType"] = Field("SexType", readOnly=True)


class SpeciesType(BaseType):
    """Identifier for species of the sample"""

    schemaKey: Literal["SpeciesType"] = Field("SpeciesType", readOnly=True)


class Disorder(BaseType):
    """Biolink, SNOMED, or other identifier for disorder studied"""

    dxdate: Optional[List[Union[date, datetime]]] = Field(
        None,
        title="Dates of diagnosis",
        description="Dates of diagnosis",
        nskey="dandi",
        rangeIncludes="schema:Date",
    )
    schemaKey: Literal["Disorder"] = Field("Disorder", readOnly=True)


class GenericType(BaseType):
    """An object to capture any type for about"""

    schemaKey: Literal["GenericType"] = Field("GenericType", readOnly=True)


class ApproachType(BaseType):
    """Identifier for approach used"""

    schemaKey: Literal["ApproachType"] = Field("ApproachType", readOnly=True)


class MeasurementTechniqueType(BaseType):
    """Identifier for measurement technique used"""

    schemaKey: Literal["MeasurementTechniqueType"] = Field(
        "MeasurementTechniqueType", readOnly=True
    )


class StandardsType(BaseType):
    """Identifier for data standard used"""

    schemaKey: Literal["StandardsType"] = Field("StandardsType", readOnly=True)


nwb_standard = StandardsType(
    name="Neurodata Without Borders (NWB)",
    identifier="RRID:SCR_015242",
).json_dict()


bids_standard = StandardsType(
    name="Brain Imaging Data Structure (BIDS)",
    identifier="RRID:SCR_016124",
).json_dict()


class ContactPoint(DandiBaseModel):
    email: Optional[EmailStr] = Field(
        None, description="Email address of contact.", nskey="schema"
    )
    url: Optional[AnyHttpUrl] = Field(
        None,
        description="A Web page to find information on how to contact.",
        nskey="schema",
    )
    schemaKey: Literal["ContactPoint"] = Field("ContactPoint", readOnly=True)

    _ldmeta = {"nskey": "schema"}


class Contributor(DandiBaseModel):
    identifier: Optional[Identifier] = Field(
        None,
        title="A common identifier",
        description="Use a common identifier such as ORCID (orcid.org) for "
        "people or ROR (ror.org) for institutions.",
        nskey="schema",
    )
    name: Optional[str] = Field(None, nskey="schema")
    email: Optional[EmailStr] = Field(None, nskey="schema")
    url: Optional[AnyHttpUrl] = Field(None, nskey="schema")
    roleName: Optional[List[RoleType]] = Field(
        None,
        title="Role",
        description="Role(s) of the contributor. Multiple roles can be selected.",
        nskey="schema",
    )
    includeInCitation: bool = Field(
        True,
        title="Include contributor in citation",
        description="A flag to indicate whether a contributor should be included "
        "when generating a citation for the item.",
        nskey="dandi",
    )
    awardNumber: Optional[Identifier] = Field(
        None,
        title="Identifier for an award",
        description="Identifier associated with a sponsored or gift award.",
        nskey="dandi",
    )
    schemaKey: Literal["Contributor"] = Field("Contributor", readOnly=True)


class Organization(Contributor):
    identifier: Optional[RORID] = Field(
        None,
        title="A ror.org identifier",
        description="Use an ror.org identifier for institutions.",
        regex=r"^https://ror.org/[a-z0-9]+$",
        nskey="schema",
    )

    includeInCitation: bool = Field(
        False,
        title="Include contributor in citation",
        description="A flag to indicate whether a contributor should be included "
        "when generating a citation for the item",
        nskey="dandi",
    )
    contactPoint: Optional[List[ContactPoint]] = Field(
        None,
        title="Organization contact information",
        description="Contact for the organization",
        nskey="schema",
    )
    schemaKey: Literal["Organization"] = Field("Organization", readOnly=True)
    _ldmeta = {
        "rdfs:subClassOf": ["schema:Organization", "prov:Organization"],
        "nskey": "dandi",
    }


class Affiliation(DandiBaseModel):
    identifier: Optional[RORID] = Field(
        None,
        title="A ror.org identifier",
        description="Use an ror.org identifier for institutions.",
        regex=r"^https://ror.org/[a-z0-9]+$",
        nskey="schema",
    )
    name: str = Field(nskey="schema", description="Name of organization")
    schemaKey: Literal["Affiliation"] = Field("Affiliation", readOnly=True)

    _ldmeta = {
        "rdfs:subClassOf": ["schema:Organization", "prov:Organization"],
        "nskey": "dandi",
    }


class Person(Contributor):
    identifier: Optional[ORCID] = Field(
        None,
        title="An ORCID identifier",
        description="An ORCID (orcid.org) identifier for an individual.",
        regex=r"^\d{4}-\d{4}-\d{4}-(\d{3}X|\d{4})$",
        nskey="schema",
    )
    name: str = Field(
        description="Use the format: familyname, given names ...",
        regex=NAME_PATTERN,
        nskey="schema",
        examples=["Lovelace, Augusta Ada", "Smith, John", "Chan, Kong-sang"],
    )
    affiliation: Optional[List[Affiliation]] = Field(
        None,
        description="An organization that this person is affiliated with.",
        nskey="schema",
    )
    schemaKey: Literal["Person"] = Field("Person", readOnly=True)

    _ldmeta = {"rdfs:subClassOf": ["schema:Person", "prov:Person"], "nskey": "dandi"}


class Software(DandiBaseModel):
    identifier: Optional[RRID] = Field(
        None,
        regex=r"^RRID\:.*",
        title="Research resource identifier",
        description="RRID of the software from scicrunch.org.",
        nskey="schema",
    )
    name: str = Field(nskey="schema")
    version: str = Field(nskey="schema")
    url: Optional[AnyHttpUrl] = Field(
        None, description="Web page for the software.", nskey="schema"
    )
    schemaKey: Literal["Software"] = Field("Software", readOnly=True)

    _ldmeta = {
        "rdfs:subClassOf": ["schema:SoftwareApplication", "prov:Software"],
        "nskey": "dandi",
    }


class Agent(DandiBaseModel):
    identifier: Optional[Identifier] = Field(
        None,
        title="Identifier",
        description="Identifier for an agent.",
        nskey="schema",
    )
    name: str = Field(nskey="schema")
    url: Optional[AnyHttpUrl] = Field(None, nskey="schema")
    schemaKey: Literal["Agent"] = Field("Agent", readOnly=True)

    _ldmeta = {
        "rdfs:subClassOf": ["prov:Agent"],
        "nskey": "dandi",
    }


class EthicsApproval(DandiBaseModel):
    """Information about ethics committee approval for project"""

    identifier: Identifier = Field(
        nskey="schema",
        title="Approved protocol identifier",
        description="Approved Protocol identifier, often a number or alphanumeric string.",
    )
    contactPoint: Optional[ContactPoint] = Field(
        None,
        description="Information about the ethics approval committee.",
        nskey="schema",
    )
    schemaKey: Literal["EthicsApproval"] = Field("EthicsApproval", readOnly=True)

    _ldmeta = {"rdfs:subClassOf": ["schema:Thing", "prov:Entity"], "nskey": "dandi"}


class Resource(DandiBaseModel):
    identifier: Optional[Identifier] = Field(None, nskey="schema")
    name: Optional[str] = Field(None, title="A title of the resource", nskey="schema")
    url: Optional[AnyHttpUrl] = Field(None, title="URL of the resource", nskey="schema")
    repository: Optional[str] = Field(
        None,
        title="Name of the repository",
        description="Name of the repository in which the resource is housed.",
        nskey="dandi",
    )
    relation: RelationType = Field(
        title="Resource relation",
        description="Indicates how the resource is related to the dataset. "
        "This relation should satisfy: dandiset <relation> resource.",
        nskey="dandi",
    )
    schemaKey: Literal["Resource"] = Field("Resource", readOnly=True)

    _ldmeta = {
        "rdfs:subClassOf": ["schema:CreativeWork", "prov:Entity"],
        "rdfs:comment": "A resource related to the project (e.g., another "
        "dataset, publication, Webpage)",
        "nskey": "dandi",
    }

    @root_validator
    def identifier_or_url(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        identifier, url = values.get("identifier"), values.get("url")
        if identifier is None and url is None:
            raise ValueError("Both identifier and url cannot be None")
        return values


class AccessRequirements(DandiBaseModel):
    """Information about access options for the dataset"""

    status: AccessType = Field(
        title="Access status",
        description="The access status of the item.",
        nskey="dandi",
    )
    contactPoint: Optional[ContactPoint] = Field(
        None,
        description="Who or where to look for information about access.",
        nskey="schema",
    )
    description: Optional[str] = Field(
        None,
        description="Information about access requirements when embargoed or restricted",
        nskey="schema",
    )
    embargoedUntil: Optional[date] = Field(
        None,
        title="Embargo end date",
        description="Date on which embargo ends.",
        readOnly=True,
        nskey="dandi",
        rangeIncludes="schema:Date",
    )
    schemaKey: Literal["AccessRequirements"] = Field(
        "AccessRequirements", readOnly=True
    )

    _ldmeta = {"rdfs:subClassOf": ["schema:Thing", "prov:Entity"], "nskey": "dandi"}

    @root_validator
    def open_or_embargoed(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        status, embargoed = values.get("status"), values.get("embargoedUntil")
        if status == AccessType.EmbargoedAccess and embargoed is None:
            raise ValueError(
                "An embargo end date is required for NIH awards to be in "
                "compliance with NIH resource sharing policy."
            )
        return values


class AssetsSummary(DandiBaseModel):
    """Summary over assets contained in a dandiset (published or not)"""

    # stats which are not stats
    numberOfBytes: int = Field(readOnly=True, sameas="schema:contentSize")
    numberOfFiles: int = Field(readOnly=True)  # universe
    numberOfSubjects: Optional[int] = Field(None, readOnly=True)  # NWB + BIDS
    numberOfSamples: Optional[int] = Field(None, readOnly=True)  # more of NWB
    numberOfCells: Optional[int] = Field(None, readOnly=True)

    dataStandard: Optional[List[StandardsType]] = Field(readOnly=True)
    # Web UI: icons per each modality?
    approach: Optional[List[ApproachType]] = Field(readOnly=True)
    # Web UI: could be an icon with number, which if hovered on  show a list?
    measurementTechnique: Optional[List[MeasurementTechniqueType]] = Field(
        readOnly=True, nskey="schema"
    )
    variableMeasured: Optional[List[str]] = Field(None, readOnly=True, nskey="schema")

    species: Optional[List[SpeciesType]] = Field(readOnly=True)
    schemaKey: Literal["AssetsSummary"] = Field("AssetsSummary", readOnly=True)

    _ldmeta = {
        "rdfs:subClassOf": ["schema:CreativeWork", "prov:Entity"],
        "nskey": "dandi",
    }


class Equipment(DandiBaseModel):
    identifier: Optional[Identifier] = Field(None, nskey="schema")
    name: str = Field(
        title="Title",
        description="A name for the equipment.",
        max_length=150,
        nskey="schema",
    )
    description: Optional[str] = Field(
        None, description="The description of the equipment.", nskey="schema"
    )
    schemaKey: Literal["Equipment"] = Field("Equipment", readOnly=True)

    _ldmeta = {
        "rdfs:subClassOf": ["schema:CreativeWork", "prov:Entity"],
        "nskey": "dandi",
    }


class Activity(DandiBaseModel):
    """Information about the Project activity"""

    identifier: Optional[Identifier] = Field(None, nskey="schema")
    name: str = Field(
        title="Title",
        description="The name of the activity.",
        max_length=150,
        nskey="schema",
    )
    description: Optional[str] = Field(
        None, description="The description of the activity.", nskey="schema"
    )
    startDate: Optional[datetime] = Field(None, nskey="schema")
    endDate: Optional[datetime] = Field(None, nskey="schema")

    # isPartOf: Optional["Activity"] = Field(None, nskey="schema")
    # hasPart: Optional["Activity"] = Field(None, nskey="schema")
    wasAssociatedWith: Optional[
        List[Union[Person, Organization, Software, Agent]]
    ] = Field(None, nskey="prov")
    used: Optional[List[Equipment]] = Field(
        None, description="A listing of equipment used for the activity.", nskey="prov"
    )
    schemaKey: Literal["Activity"] = Field("Activity", readOnly=True)

    _ldmeta = {"rdfs:subClassOf": ["prov:Activity", "schema:Thing"], "nskey": "dandi"}


class Project(Activity):
    name: str = Field(
        title="Name of project",
        description="The name of the project that generated this Dandiset or asset.",
        max_length=150,
        nskey="schema",
    )
    description: Optional[str] = Field(
        None, description="A brief description of the project.", nskey="schema"
    )
    schemaKey: Literal["Project"] = Field("Project", readOnly=True)


class Session(Activity):
    name: str = Field(
        title="Name of session",
        description="The name of the logical session associated with the asset.",
        max_length=150,
        nskey="schema",
    )
    description: Optional[str] = Field(
        None, description="A brief description of the session.", nskey="schema"
    )
    schemaKey: Literal["Session"] = Field("Session", readOnly=True)


class PublishActivity(Activity):
    schemaKey: Literal["PublishActivity"] = Field("PublishActivity", readOnly=True)


class Locus(DandiBaseModel):
    identifier: Union[Identifier, List[Identifier]] = Field(
        description="Identifier for genotyping locus.", nskey="schema"
    )
    locusType: Optional[str] = Field(None)
    schemaKey: Literal["Locus"] = Field("Locus", readOnly=True)
    _ldmeta = {"nskey": "dandi"}


class Allele(DandiBaseModel):
    identifier: Union[Identifier, List[Identifier]] = Field(
        description="Identifier for genotyping allele.", nskey="schema"
    )
    alleleSymbol: Optional[str] = Field(None)
    alleleType: Optional[str] = Field(None)
    schemaKey: Literal["Allele"] = Field("Allele", readOnly=True)
    _ldmeta = {"nskey": "dandi"}


class GenotypeInfo(DandiBaseModel):
    locus: Locus = Field(description="Locus at which information was extracted.")
    alleles: List[Allele] = Field(description="Information about alleles at the locus.")
    wasGeneratedBy: Optional[List["Session"]] = Field(
        None,
        description="Information about session activity used to determine genotype.",
        nskey="prov",
    )
    schemaKey: Literal["GenotypeInfo"] = Field("GenotypeInfo", readOnly=True)
    _ldmeta = {"nskey": "dandi"}


class RelatedParticipant(DandiBaseModel):
    identifier: Optional[Identifier] = Field(None, nskey="schema")
    name: Optional[str] = Field(
        None, title="Name of the participant or subject", nskey="schema"
    )
    url: Optional[AnyHttpUrl] = Field(
        None, title="URL of the related participant or subject", nskey="schema"
    )
    relation: ParticipantRelationType = Field(
        title="Participant or subject relation",
        description="Indicates how the current participant or subject is related "
        "to the other participant or subject. This relation should "
        "satisfy: Participant/Subject <relation> relatedParticipant/Subject.",
        nskey="dandi",
    )
    schemaKey: Literal["RelatedParticipant"] = Field(
        "RelatedParticipant", readOnly=True
    )

    _ldmeta = {
        "rdfs:subClassOf": ["schema:CreativeWork", "prov:Entity"],
        "rdfs:comment": "Another participant or subject related to the current "
        "participant or subject (e.g., another parent, sibling, child).",
        "nskey": "dandi",
    }


class Participant(DandiBaseModel):
    """Description about the Participant or Subject studied.

    The Participant or Subject can be any individual or synthesized Agent. The
    properties of the Participant or Subject refers to information at the timepoint
    when the Participant or Subject engaged in the production of data being described.
    """

    identifier: Identifier = Field(nskey="schema")
    altName: Optional[List[Identifier]] = Field(None, nskey="dandi")

    strain: Optional[StrainType] = Field(
        None,
        description="Identifier for the strain of the participant or subject.",
        nskey="dandi",
    )
    cellLine: Optional[Identifier] = Field(
        None,
        description="Cell line associated with the participant or subject.",
        nskey="dandi",
    )
    vendor: Optional[Organization] = Field(None, nskey="dandi")
    age: Optional[PropertyValue] = Field(
        None,
        description="A representation of age using ISO 8601 duration. This "
        "should include a valueReference if anything other than "
        "date of birth is used.",
        nskey="dandi",
        rangeIncludes="schema:Duration",
    )

    sex: Optional[SexType] = Field(
        None,
        description="Identifier for sex of the participant or subject if "
        "available. (e.g. from OBI)",
        nskey="dandi",
    )
    genotype: Optional[Union[List[GenotypeInfo], Identifier]] = Field(
        None,
        description="Genotype descriptor of participant or subject if available",
        nskey="dandi",
    )
    species: Optional[SpeciesType] = Field(
        None,
        description="An identifier indicating the taxonomic classification of "
        "the participant or subject.",
        nskey="dandi",
    )
    disorder: Optional[List[Disorder]] = Field(
        None,
        description="Any current diagnosed disease or disorder associated with "
        "the participant or subject.",
        nskey="dandi",
    )

    relatedParticipant: Optional[List[RelatedParticipant]] = Field(
        None,
        description="Information about related participants or subjects in a "
        "study or across studies.",
        nskey="dandi",
    )
    sameAs: Optional[List[Identifier]] = Field(
        None,
        description="An identifier to link participants or subjects across datasets.",
        nskey="schema",
    )
    schemaKey: Literal["Participant"] = Field("Participant", readOnly=True)

    _ldmeta = {
        "rdfs:subClassOf": ["prov:Agent"],
        "rdfs:label": "Information about the participant or subject.",
        "nskey": "dandi",
    }


class BioSample(DandiBaseModel):
    """Description of the sample that was studied"""

    identifier: Identifier = Field(nskey="schema")
    sampleType: SampleType = Field(
        description="Identifier for the sample characteristics (e.g., from OBI, Encode).",
        nskey="dandi",
    )
    assayType: Optional[List[AssayType]] = Field(
        None, description="Identifier for the assay(s) used (e.g., OBI).", nskey="dandi"
    )
    anatomy: Optional[List[Anatomy]] = Field(
        None,
        description="Identifier for what organ the sample belongs "
        "to. Use the most specific descriptor from sources such as UBERON.",
        nskey="dandi",
    )

    wasDerivedFrom: Optional[List["BioSample"]] = Field(
        None,
        description="Describes the hierarchy of sample derivation or aggregation.",
        nskey="prov",
    )
    wasAttributedTo: Optional[List[Participant]] = Field(
        None,
        description="Participant(s) or Subject(s) associated with this sample.",
        nskey="prov",
    )
    sameAs: Optional[List[Identifier]] = Field(None, nskey="schema")
    hasMember: Optional[List[Identifier]] = Field(None, nskey="prov")
    schemaKey: Literal["BioSample"] = Field("BioSample", readOnly=True)

    _ldmeta = {
        "rdfs:subClassOf": ["schema:Thing", "prov:Entity"],
        "rdfs:label": "Information about the biosample.",
        "nskey": "dandi",
    }


BioSample.update_forward_refs()


class CommonModel(DandiBaseModel):
    schemaVersion: str = Field(
        default=DANDI_SCHEMA_VERSION, readOnly=True, nskey="schema"
    )
    name: Optional[str] = Field(
        None,
        title="Title",
        description="The name of the item.",
        max_length=150,
        nskey="schema",
    )
    description: Optional[str] = Field(
        None, description="A description of the item.", nskey="schema"
    )
    contributor: Optional[List[Union[Person, Organization]]] = Field(
        None,
        title="Contributors",
        description="Contributors to this item: persons or organizations.",
        nskey="schema",
    )
    about: Optional[List[Union[Disorder, Anatomy, GenericType]]] = Field(
        None,
        title="Subject matter of the dataset",
        description="The subject matter of the content, such as disorders, brain anatomy.",
        nskey="schema",
    )
    studyTarget: Optional[List[str]] = Field(
        None,
        description="Objectives or specific questions of the study.",
        nskey="dandi",
    )
    license: Optional[List[LicenseType]] = Field(
        None,
        description="Licenses associated with the item. DANDI only supports a "
        "subset of Creative Commons Licenses (creativecommons.org) "
        "applicable to datasets.",
        nskey="schema",
    )
    protocol: Optional[List[AnyHttpUrl]] = Field(
        None,
        description="A list of persistent URLs describing the protocol (e.g. "
        "protocols.io, or other DOIs).",
        nskey="dandi",
    )
    ethicsApproval: Optional[List[EthicsApproval]] = Field(
        None, title="Ethics approvals", nskey="dandi"
    )
    keywords: Optional[List[str]] = Field(
        None,
        description="Keywords used to describe this content.",
        nskey="schema",
    )
    acknowledgement: Optional[str] = Field(
        None,
        descriptions="Any acknowledgments not covered by contributors or external resources.",
        nskey="dandi",
    )

    # Linking to this dandiset or the larger thing
    access: List[AccessRequirements] = Field(
        title="Access information",
        default_factory=lambda: [AccessRequirements(status=AccessType.OpenAccess)],
        nskey="dandi",
        readOnly=True,
    )
    url: Optional[AnyHttpUrl] = Field(
        None, readOnly=True, description="permalink to the item", nskey="schema"
    )
    repository: AnyHttpUrl = Field(
        # mypy doesn't like using a string as the default for an AnyHttpUrl
        # attribute, so we have to convert it to an AnyHttpUrl:
        parse_obj_as(AnyHttpUrl, DANDI_INSTANCE_URL),
        readOnly=True,
        description="location of the item",
        nskey="dandi",
    )
    relatedResource: Optional[List[Resource]] = Field(None, nskey="dandi")

    wasGeneratedBy: Optional[List[Activity]] = Field(None, nskey="prov")
    schemaKey: Literal["CommonModel"] = Field("CommonModel", readOnly=True)


class Dandiset(CommonModel):
    """A body of structured information describing a DANDI dataset."""

    @validator("contributor")
    def contributor_musthave_contact(
        cls, values: List[Union[Person, Organization]]
    ) -> List[Union[Person, Organization]]:
        contacts = []
        for val in values:
            if val.roleName and RoleType.ContactPerson in val.roleName:
                contacts.append(val)
        if len(contacts) == 0:
            raise ValueError("At least one contributor must have role ContactPerson")
        return values

    id: str = Field(
        description="Uniform resource identifier",
        regex=r"^(dandi|DANDI):\d{6}(/(draft|\d+\.\d+\.\d+))$",
        readOnly=True,
    )

    identifier: DANDI = Field(
        readOnly=True,
        title="Dandiset identifier",
        description="A Dandiset identifier that can be resolved by identifiers.org.",
        regex=r"^DANDI\:\d{6}$",
        nskey="schema",
    )
    name: str = Field(
        title="Dandiset title",
        description="A title associated with the Dandiset.",
        max_length=150,
        nskey="schema",
    )
    description: str = Field(
        description="A description of the Dandiset", max_length=3000, nskey="schema"
    )
    contributor: List[Union[Person, Organization]] = Field(
        title="Dandiset contributors",
        description="People or Organizations that have contributed to this Dandiset.",
        nskey="schema",
        min_items=1,
    )
    dateCreated: Optional[datetime] = Field(
        None, nskey="schema", title="Dandiset creation date and time.", readOnly=True
    )
    dateModified: Optional[datetime] = Field(
        None, nskey="schema", title="Last modification date and time.", readOnly=True
    )

    license: List[LicenseType] = Field(
        min_items=1,
        description="Licenses associated with the item. DANDI only supports a "
        "subset of Creative Commons Licenses (creativecommons.org) "
        "applicable to datasets.",
        nskey="schema",
    )

    citation: str = Field(readOnly=True, nskey="schema")

    # From assets
    assetsSummary: AssetsSummary = Field(readOnly=True, nskey="dandi")

    # From server (requested by users even for drafts)
    manifestLocation: List[AnyHttpUrl] = Field(
        readOnly=True, min_items=1, nskey="dandi"
    )

    version: str = Field(readOnly=True, nskey="schema")

    wasGeneratedBy: Optional[List[Project]] = Field(
        None,
        title="Associated projects",
        description="Project(s) that generated this Dandiset.",
        nskey="prov",
    )

    schemaKey: Literal["Dandiset"] = Field("Dandiset", readOnly=True)

    _ldmeta = {
        "rdfs:subClassOf": ["schema:Dataset", "prov:Entity"],
        "rdfs:label": "Information about the dataset",
        "nskey": "dandi",
    }


class BareAsset(CommonModel):
    """Metadata used to describe an asset anywhere (local or server).

    Derived from C2M2 (Level 0 and 1) and schema.org
    """

    contentSize: ByteSize = Field(nskey="schema")
    encodingFormat: Union[AnyHttpUrl, str] = Field(
        title="File encoding format", nskey="schema"
    )
    digest: Dict[DigestType, str] = Field(
        title="A map of dandi digests to their values", nskey="dandi"
    )
    path: str = Field(nskey="dandi")

    dateModified: Optional[datetime] = Field(
        None,
        nskey="schema",
        title="Asset (file or metadata) modification date and time",
    )
    blobDateModified: Optional[datetime] = Field(
        None, nskey="dandi", title="Asset file modification date and time."
    )
    # overload to restrict with max_items=1
    access: List[AccessRequirements] = Field(
        title="Access information",
        default_factory=lambda: [AccessRequirements(status=AccessType.OpenAccess)],
        nskey="dandi",
        max_items=1,
    )

    # this is from C2M2 level 1 - using EDAM vocabularies - in our case we would
    # need to come up with things for neurophys
    # TODO: waiting on input <https://github.com/dandi/dandi-cli/pull/226>
    dataType: Optional[AnyHttpUrl] = Field(None, nskey="dandi")

    sameAs: Optional[List[AnyHttpUrl]] = Field(None, nskey="schema")

    # TODO
    approach: Optional[List[ApproachType]] = Field(None, readOnly=True, nskey="dandi")
    measurementTechnique: Optional[List[MeasurementTechniqueType]] = Field(
        None, readOnly=True, nskey="schema"
    )
    variableMeasured: Optional[List[PropertyValue]] = Field(
        None, readOnly=True, nskey="schema"
    )

    wasDerivedFrom: Optional[List[BioSample]] = Field(None, nskey="prov")
    wasAttributedTo: Optional[List[Participant]] = Field(
        None,
        description="Associated participant(s) or subject(s).",
        nskey="prov",
    )
    wasGeneratedBy: Optional[List[Union[Session, Project, Activity]]] = Field(
        None,
        title="Name of the session, project or activity.",
        description="Describe the session, project or activity that generated this asset.",
        nskey="prov",
    )

    # Bare asset is to be just Asset.
    schemaKey: Literal["Asset"] = Field("Asset", readOnly=True)

    _ldmeta = {
        "rdfs:subClassOf": ["schema:CreativeWork", "prov:Entity"],
        "rdfs:label": "Information about the asset",
        "nskey": "dandi",
    }

    @validator("digest")
    def digest_check(
        cls, v: Dict[DigestType, str], values: Dict[str, Any], **kwargs: Any
    ) -> Dict[DigestType, str]:
        if values.get("encodingFormat") == "application/x-zarr":
            if DigestType.dandi_zarr_checksum not in v:
                raise ValueError("A zarr asset must have a zarr checksum.")
            if v.get(DigestType.dandi_etag):
                raise ValueError("Digest cannot have both etag and zarr checksums.")
            digest = v[DigestType.dandi_zarr_checksum]
            if not re.fullmatch(ZARR_CHECKSUM_PATTERN, digest):
                raise ValueError(
                    f"Digest must have an appropriate dandi-zarr-checksum value. "
                    f"Got {digest}"
                )
            _checksum, _file_count, zarr_size = parse_directory_digest(digest)
            content_size = values.get("contentSize")
            if content_size != zarr_size:
                raise ValueError(
                    f"contentSize {content_size} is not equal to the checksum size {zarr_size}."
                )
        else:
            if DigestType.dandi_etag not in v:
                raise ValueError("A non-zarr asset must have a dandi-etag.")
            if v.get(DigestType.dandi_zarr_checksum):
                raise ValueError("Digest cannot have both etag and zarr checksums.")
            digest = v[DigestType.dandi_etag]
            if not re.fullmatch(DandiETag.REGEX, digest):
                raise ValueError(
                    f"Digest must have an appropriate dandi-etag value. "
                    f"Got {digest}"
                )
        return v


class Asset(BareAsset):
    """Metadata used to describe an asset on the server."""

    # all of the following are set by server
    id: str = Field(readOnly=True, description="Uniform resource identifier.")
    identifier: UUID4 = Field(readOnly=True, nskey="schema")
    contentUrl: List[AnyHttpUrl] = Field(readOnly=True, nskey="schema")


class Publishable(DandiBaseModel):
    publishedBy: Union[AnyHttpUrl, PublishActivity] = Field(
        description="The URL should contain the provenance of the publishing process.",
        readOnly=True,
        nskey="dandi",
    )
    datePublished: datetime = Field(readOnly=True, nskey="schema")
    schemaKey: Literal["Publishable"] = Field("Publishable", readOnly=True)


class PublishedDandiset(Dandiset, Publishable):
    id: str = Field(
        description="Uniform resource identifier.",
        regex=DANDI_PUBID_PATTERN,
        readOnly=True,
    )

    doi: str = Field(
        title="DOI",
        readOnly=True,
        regex=DANDI_DOI_PATTERN,
        nskey="dandi",
    )
    url: AnyHttpUrl = Field(
        readOnly=True,
        description="Permalink to the Dandiset.",
        nskey="schema",
    )

    schemaKey: Literal["Dandiset"] = Field("Dandiset", readOnly=True)

    @validator("assetsSummary")
    def check_filesbytes(cls, values: AssetsSummary) -> AssetsSummary:
        if values.numberOfBytes == 0 or values.numberOfFiles == 0:
            raise ValueError(
                "A Dandiset containing no files or zero bytes is not publishable"
            )
        return values

    @validator("url")
    def check_url(cls, url: AnyHttpUrl) -> AnyHttpUrl:
        if not re.match(PUBLISHED_VERSION_URL_PATTERN, str(url)):
            raise ValueError(
                f'string does not match regex "{PUBLISHED_VERSION_URL_PATTERN}"'
            )
        return url


class PublishedAsset(Asset, Publishable):
    id: str = Field(
        description="Uniform resource identifier.",
        regex=ASSET_UUID_PATTERN,
        readOnly=True,
    )

    schemaKey: Literal["Asset"] = Field("Asset", readOnly=True)

    @validator("digest")
    def digest_sha256check(
        cls, v: Dict[DigestType, str], values: Dict[str, Any], **kwargs: Any
    ) -> Dict[DigestType, str]:
        if values.get("encodingFormat") != "application/x-zarr":
            if DigestType.sha2_256 not in v:
                raise ValueError("A non-zarr asset must have a sha2_256.")
            digest = v[DigestType.sha2_256]
            if not re.fullmatch(SHA256_PATTERN, digest):
                raise ValueError(
                    f"Digest must have an appropriate sha2_256 value. Got {digest}"
                )
        return v


def get_schema_version() -> str:
    return DANDI_SCHEMA_VERSION
