from __future__ import annotations

import re
from datetime import date, datetime
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
)
from warnings import warn

from pydantic import (
    UUID4,
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    GetJsonSchemaHandler,
    StringConstraints,
    TypeAdapter,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema
from zarr_checksum.checksum import InvalidZarrChecksum, ZarrDirectoryDigest

from dandischema.conf import (
    DEFAULT_INSTANCE_NAME,
    UNVENDORED_DOI_PREFIX_PATTERN,
    UNVENDORED_ID_PATTERN,
    get_instance_config,
)

from .consts import (
    ASSET_UUID_PATTERN,
    DANDI_NSKEY,
    DANDI_SCHEMA_VERSION,
    NAME_PATTERN,
    SHA256_PATTERN,
)
from .digests.dandietag import DandiETag
from .types import ByteSizeJsonSchema
from .utils import name2title

M = TypeVar("M", bound=BaseModel)


def diff_models(model1: M, model2: M) -> None:
    """Perform a field-wise diff"""
    for field in model1.model_fields:
        if getattr(model1, field) != getattr(model2, field):
            print(f"{field} is different")


if TYPE_CHECKING:
    # This is just a placeholder for static type checking
    class LicenseType(Enum): ...  # fmt: skip

else:
    LicenseType = Enum(
        "LicenseType",
        [(license_.name, license_.value) for license_ in _INSTANCE_CONFIG.licenses],
    )
    r"""
    An enumeration of supported licenses

    The value of each member is a string that matches the regex pattern of
    `^([^:\s]+):(\S+)$` in which the first group matches the license scheme such
    as `"spdx"`, and the second group matches the license identifier such as
    `"CC-BY-4.0"`.
    """


class AccessType(Enum):
    """An enumeration of access status options"""

    #: The dandiset is openly accessible
    OpenAccess = f"{DANDI_NSKEY}:OpenAccess"

    #: The dandiset is embargoed
    EmbargoedAccess = f"{DANDI_NSKEY}:EmbargoedAccess"

    """
    Uncomment when restricted access is implemented:
        #: The dandiset is restricted
        RestrictedAccess = f"{DANDI_NSKEY}:RestrictedAccess"
    """


class DigestType(Enum):
    """An enumeration of checksum types"""

    #: MD5 checksum
    md5 = f"{DANDI_NSKEY}:md5"

    #: SHA1 checksum
    sha1 = f"{DANDI_NSKEY}:sha1"

    #: SHA2-256 checksum
    sha2_256 = f"{DANDI_NSKEY}:sha2-256"

    #: SHA3-256 checksum
    sha3_256 = f"{DANDI_NSKEY}:sha3-256"

    #: BLAKE2B-256 checksum
    blake2b_256 = f"{DANDI_NSKEY}:blake2b-256"

    #: BLAKE3-256 checksum
    blake3 = f"{DANDI_NSKEY}:blake3"

    #: S3-style ETag
    dandi_etag = f"{DANDI_NSKEY}:dandi-etag"

    #: DANDI Zarr checksum
    dandi_zarr_checksum = f"{DANDI_NSKEY}:dandi-zarr-checksum"


class IdentifierType(Enum):
    """An enumeration of identifiers"""

    doi = f"{DANDI_NSKEY}:doi"
    orcid = f"{DANDI_NSKEY}:orcid"
    ror = f"{DANDI_NSKEY}:ror"
    dandi = f"{DANDI_NSKEY}:dandi"
    rrid = f"{DANDI_NSKEY}:rrid"


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
    isChildOf = f"{DANDI_NSKEY}:isChildOf"

    #: Indicates that A is a parent of B
    isParentOf = f"{DANDI_NSKEY}:isParentOf"

    #: Indicates that A is a sibling of B
    isSiblingOf = f"{DANDI_NSKEY}:isSiblingOf"

    #: Indicates that A is a monozygotic twin of B
    isMonozygoticTwinOf = f"{DANDI_NSKEY}:isMonozygoticTwinOf"

    #: Indicates that A is a dizygotic twin of B
    isDizygoticTwinOf = f"{DANDI_NSKEY}:isDizygoticTwinOf"


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


class ResourceType(Enum):
    """An enumeration of resource types"""

    #: Audiovisual: A series of visual representations imparting an impression of motion
    # when shown in succession. May or may not include sound.
    Audiovisual = "dcite:Audiovisual"

    #: Book: A medium for recording information in the form of writing or images,
    # typically composed of many pages bound together and protected by a cover.
    Book = "dcite:Book"

    #: BookChapter: One of the main divisions of a book.
    BookChapter = "dcite:BookChapter"

    #: Collection: An aggregation of resources, which may encompass collections of one
    # resourceType as well as those of mixed types. A collection is described as a
    # group; its parts may also be separately described.
    Collection = "dcite:Collection"

    #: ComputationalNotebook: A virtual notebook environment used for literate
    # programming.
    ComputationalNotebook = "dcite:ComputationalNotebook"

    #: ConferencePaper: Article that is written with the goal of being accepted to a
    # conference.
    ConferencePaper = "dcite:ConferencePaper"

    #: ConferenceProceeding: Collection of academic papers published in the context of
    # an academic conference.
    ConferenceProceeding = "dcite:ConferenceProceeding"

    #: DataPaper: A factual and objective publication with a focused intent to identify
    # and describe specific data, sets of data, or data collections to facilitate
    # discoverability.
    DataPaper = "dcite:DataPaper"

    #: Dataset: Data encoded in a defined structure.
    Dataset = "dcite:Dataset"

    #: Dissertation: A written essay, treatise, or thesis, especially one written by a
    # candidate for the degree of Doctor of Philosophy.
    Dissertation = "dcite:Dissertation"

    #: Event: A non-persistent, time-based occurrence.
    Event = "dcite:Event"

    #: Image: A visual representation other than text.
    Image = "dcite:Image"

    #: Instrument: A device, tool or apparatus used to obtain, measure and/or analyze
    # data.
    Instrument = "dcite:Instrument"

    #: InteractiveResource: A resource requiring interaction from the user to be
    # understood, executed, or experienced.
    InteractiveResource = "dcite:InteractiveResource"

    #: Journal: A scholarly publication consisting of articles that is published
    # regularly throughout the year.
    Journal = "dcite:Journal"

    #: JournalArticle: A written composition on a topic of interest, which forms a
    # separate part of a journal.
    JournalArticle = "dcite:JournalArticle"

    #: Model: An abstract, conceptual, graphical, mathematical or visualization model
    # that represents empirical objects, phenomena, or physical processes.
    Model = "dcite:Model"

    #: OutputManagementPlan: A formal document that outlines how research outputs are to
    # be handled both during a research project and after the project is completed.
    OutputManagementPlan = "dcite:OutputManagementPlan"

    #: PeerReview: Evaluation of scientific, academic, or professional work by others
    # working in the same field.
    PeerReview = "dcite:PeerReview"

    #: PhysicalObject: A physical object or substance.
    PhysicalObject = "dcite:PhysicalObject"

    #: Preprint: A version of a scholarly or scientific paper that precedes formal peer
    # review and publication in a peer-reviewed scholarly or scientific journal.
    Preprint = "dcite:Preprint"

    #: Report: A document that presents information in an organized format for a
    # specific audience and purpose.
    Report = "dcite:Report"

    #: Service: An organized system of apparatus, appliances, staff, etc., for supplying
    # some function(s) required by end users.
    Service = "dcite:Service"

    #: Software: A computer program other than a computational notebook, in either
    # source code (text) or compiled form. Use this type for general software components
    # supporting scholarly research. Use the “ComputationalNotebook” value for virtual
    # notebooks.
    Software = "dcite:Software"

    #: Sound: A resource primarily intended to be heard.
    Sound = "dcite:Sound"

    #: Standard: Something established by authority, custom, or general consent as a
    # model, example, or point of reference.
    Standard = "dcite:Standard"

    #: StudyRegistration: A detailed, time-stamped description of a research plan, often
    # openly shared in a registry or published in a journal before the study is
    # conducted to lend accountability and transparency in the hypothesis generating and
    # testing process.
    StudyRegistration = "dcite:StudyRegistration"

    #: Text: A resource consisting primarily of words for reading that is not covered by
    # any other textual resource type in this list.
    Text = "dcite:Text"

    #: Workflow: A structured series of steps which can be executed to produce a final
    # outcome, allowing users a means to specify and enact their work in a more
    # reproducible manner.
    Workflow = "dcite:Workflow"

    #: Other: A resource that does not fit into any of the other categories.
    Other = "dcite:Other"


class AgeReferenceType(Enum):
    """An enumeration of age reference"""

    #: Age since Birth
    BirthReference = f"{DANDI_NSKEY}:BirthReference"

    #: Age of a pregnancy (https://en.wikipedia.org/wiki/Gestational_age)
    GestationalReference = f"{DANDI_NSKEY}:GestationalReference"


class DandiBaseModel(BaseModel):
    id: Optional[str] = Field(
        default=None,
        description="Uniform resource identifier",
        json_schema_extra={"readOnly": True},
    )
    schemaKey: str = Field(
        "DandiBaseModel", validate_default=True, json_schema_extra={"readOnly": True}
    )

    def json_dict(self) -> dict:
        """
        Recursively convert the instance to a `dict` of JSONable values,
        including converting enum values to strings.  `None` fields
        are omitted.
        """
        warn(
            "`DandiBaseModel.json_dict()` is deprecated. Use "
            "`pydantic.BaseModel.model_dump(mode='json', exclude_none=True)` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.model_dump(mode="json", exclude_none=True)

    @field_validator("schemaKey")
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
    def unvalidated(__pydantic_cls__: Type[M], **data: Any) -> M:
        """Allow model to be returned without validation"""

        warn(
            "`DandiBaseModel.unvalidated()` is deprecated. "
            "Use `pydantic.BaseModel.model_construct()` instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return __pydantic_cls__.model_construct(**data)

    @classmethod
    def to_dictrepr(__pydantic_cls__: Type["DandiBaseModel"]) -> str:
        return (
            __pydantic_cls__.model_construct()
            .__repr__()
            .replace(__pydantic_cls__.__name__, "dict")
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema_: CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        schema = handler(core_schema_)
        schema = handler.resolve_ref_schema(schema)

        if schema["title"] == "PropertyValue":
            schema["required"] = sorted({"value"}.union(schema.get("required", [])))
        schema["title"] = name2title(schema["title"])
        if schema["type"] == "object":
            schema["required"] = sorted({"schemaKey"}.union(schema.get("required", [])))
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
                # triggers only for ROR in identifier
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

        return schema


class PropertyValue(DandiBaseModel):
    maxValue: Optional[float] = Field(None, json_schema_extra={"nskey": "schema"})
    minValue: Optional[float] = Field(None, json_schema_extra={"nskey": "schema"})
    unitText: Optional[str] = Field(None, json_schema_extra={"nskey": "schema"})
    value: Union[Any, List[Any]] = Field(
        None,
        validate_default=True,
        json_schema_extra={"nskey": "schema"},
        description="The value associated with this property.",
    )
    valueReference: Optional["PropertyValue"] = Field(
        None, json_schema_extra={"nskey": "schema"}
    )  # Note: recursive (circular or not)
    propertyID: Optional[Union[IdentifierType, AnyHttpUrl]] = Field(
        None,
        description="A commonly used identifier for "
        "the characteristic represented by the property. "
        "For example, a known prefix like DOI or a full URL.",
        json_schema_extra={"nskey": "schema"},
    )
    schemaKey: Literal["PropertyValue"] = Field(
        "PropertyValue", validate_default=True, json_schema_extra={"readOnly": True}
    )

    @field_validator("value")
    @classmethod
    def ensure_value(cls, val: Union[Any, List[Any]]) -> Union[Any, List[Any]]:
        if not val:
            raise ValueError(
                "The value field of a PropertyValue cannot be None or empty."
            )
        return val

    _ldmeta = {"nskey": "schema"}


# This is mostly not needed at all since self-referencing models
# are automatically resolved by Pydantic in a pretty consistent way even in Pydantic V1
# https://docs.pydantic.dev/1.10/usage/postponed_annotations/#self-referencing-models
# and continue to be so in Pydantic V2
# https://docs.pydantic.dev/latest/concepts/postponed_annotations/#self-referencing-or-recursive-models
PropertyValue.model_rebuild()

Identifier = str
ORCID = str
RORID = str
DANDI = str
RRID = str


class BaseType(DandiBaseModel):
    """Base class for enumerated types"""

    identifier: Optional[
        Annotated[
            Union[
                AnyHttpUrl,
                Annotated[
                    str, StringConstraints(pattern=r"^[a-zA-Z0-9-]+:[a-zA-Z0-9-/\._]+$")
                ],
            ],
            Field(union_mode="left_to_right"),
        ]
    ] = Field(
        None,
        description="The identifier can be any url or a compact URI, preferably"
        " supported by identifiers.org.",
        json_schema_extra={"nskey": "schema"},
    )
    name: Optional[str] = Field(
        None,
        description="The name of the item.",
        max_length=150,
        json_schema_extra={"nskey": "schema"},
    )
    schemaKey: str = Field(
        "BaseType", validate_default=True, json_schema_extra={"readOnly": True}
    )
    _ldmeta = {"rdfs:subClassOf": ["prov:Entity", "schema:Thing"], "nskey": DANDI_NSKEY}

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema_: CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        schema = super().__get_pydantic_json_schema__(core_schema_, handler)

        for prop, value in schema.get("properties", {}).items():
            # This check removes the anyOf field from the identifier property
            # in the schema generation. This relates to a UI issue where two
            # basic properties, in this case "string", is dropped from the UI.
            if prop == "identifier":
                for option in value.pop("anyOf", []):
                    if option.get("format", "") == "uri":
                        value.update(**option)
                        value["maxLength"] = 1000

        return schema


class AssayType(BaseType):
    """OBI based identifier for the assay(s) used"""

    schemaKey: Literal["AssayType"] = Field(
        "AssayType", validate_default=True, json_schema_extra={"readOnly": True}
    )


class SampleType(BaseType):
    """OBI based identifier for the sample type used"""

    schemaKey: Literal["SampleType"] = Field(
        "SampleType", validate_default=True, json_schema_extra={"readOnly": True}
    )


class Anatomy(BaseType):
    """UBERON or other identifier for anatomical part studied"""

    schemaKey: Literal["Anatomy"] = Field(
        "Anatomy", validate_default=True, json_schema_extra={"readOnly": True}
    )


class StrainType(BaseType):
    """Identifier for the strain of the sample"""

    schemaKey: Literal["StrainType"] = Field(
        "StrainType", validate_default=True, json_schema_extra={"readOnly": True}
    )


class SexType(BaseType):
    """Identifier for the sex of the sample"""

    schemaKey: Literal["SexType"] = Field(
        "SexType", validate_default=True, json_schema_extra={"readOnly": True}
    )


class SpeciesType(BaseType):
    """Identifier for species of the sample"""

    schemaKey: Literal["SpeciesType"] = Field(
        "SpeciesType", validate_default=True, json_schema_extra={"readOnly": True}
    )


class Disorder(BaseType):
    """Biolink, SNOMED, or other identifier for disorder studied"""

    dxdate: Optional[List[Union[date, datetime]]] = Field(
        None,
        title="Dates of diagnosis",
        description="Dates of diagnosis",
        json_schema_extra={"nskey": DANDI_NSKEY, "rangeIncludes": "schema:Date"},
    )
    schemaKey: Literal["Disorder"] = Field(
        "Disorder", validate_default=True, json_schema_extra={"readOnly": True}
    )


class GenericType(BaseType):
    """An object to capture any type for about"""

    schemaKey: Literal["GenericType"] = Field(
        "GenericType", validate_default=True, json_schema_extra={"readOnly": True}
    )


class ApproachType(BaseType):
    """Identifier for approach used"""

    schemaKey: Literal["ApproachType"] = Field(
        "ApproachType", validate_default=True, json_schema_extra={"readOnly": True}
    )


class MeasurementTechniqueType(BaseType):
    """Identifier for measurement technique used"""

    schemaKey: Literal["MeasurementTechniqueType"] = Field(
        "MeasurementTechniqueType",
        validate_default=True,
        json_schema_extra={"readOnly": True},
    )


class StandardsType(BaseType):
    """Identifier for data standard used"""

    schemaKey: Literal["StandardsType"] = Field(
        "StandardsType", validate_default=True, json_schema_extra={"readOnly": True}
    )


nwb_standard = StandardsType(
    name="Neurodata Without Borders (NWB)",
    identifier="RRID:SCR_015242",
).model_dump(mode="json", exclude_none=True)

bids_standard = StandardsType(
    name="Brain Imaging Data Structure (BIDS)",
    identifier="RRID:SCR_016124",
).model_dump(mode="json", exclude_none=True)

ome_ngff_standard = StandardsType(
    name="OME/NGFF Standard",
    identifier="DOI:10.25504/FAIRsharing.9af712",
).model_dump(mode="json", exclude_none=True)


class ContactPoint(DandiBaseModel):
    email: Optional[EmailStr] = Field(
        None,
        description="Email address of contact.",
        json_schema_extra={"nskey": "schema"},
    )
    url: Optional[AnyHttpUrl] = Field(
        None,
        description="A Web page to find information on how to contact.",
        json_schema_extra={"nskey": "schema"},
    )
    schemaKey: Literal["ContactPoint"] = Field(
        "ContactPoint", validate_default=True, json_schema_extra={"readOnly": True}
    )

    _ldmeta = {"nskey": "schema"}


class Contributor(DandiBaseModel):
    identifier: Optional[Identifier] = Field(
        None,
        title="A common identifier",
        description="Use a common identifier such as ORCID (orcid.org) for "
        "people or ROR (ror.org) for institutions.",
        json_schema_extra={"nskey": "schema"},
    )
    name: Optional[str] = Field(None, json_schema_extra={"nskey": "schema"})
    email: Optional[EmailStr] = Field(None, json_schema_extra={"nskey": "schema"})
    url: Optional[AnyHttpUrl] = Field(None, json_schema_extra={"nskey": "schema"})
    roleName: Optional[List[RoleType]] = Field(
        None,
        title="Role",
        description="Role(s) of the contributor. Multiple roles can be selected.",
        json_schema_extra={"nskey": "schema"},
    )
    includeInCitation: bool = Field(
        True,
        title="Include contributor in citation",
        description="A flag to indicate whether a contributor should be included "
        "when generating a citation for the item.",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    awardNumber: Optional[Identifier] = Field(
        None,
        title="Identifier for an award",
        description="Identifier associated with a sponsored or gift award.",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    schemaKey: Literal["Contributor", "Organization", "Person"] = Field(
        "Contributor", validate_default=True, json_schema_extra={"readOnly": True}
    )

    @model_validator(mode="after")
    def ensure_contact_person_has_email(self) -> Contributor:
        role_names = self.roleName

        if role_names is not None and RoleType.ContactPerson in role_names:
            if self.email is None:
                raise ValueError("Contact person must have an email address.")

        return self


class Organization(Contributor):
    identifier: Optional[RORID] = Field(
        None,
        title="A ror.org identifier",
        description="Use an ror.org identifier for institutions.",
        pattern=r"^https://ror.org/[a-z0-9]+$",
        json_schema_extra={"nskey": "schema"},
    )

    includeInCitation: bool = Field(
        False,
        title="Include contributor in citation",
        description="A flag to indicate whether a contributor should be included "
        "when generating a citation for the item",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    contactPoint: Optional[List[ContactPoint]] = Field(
        None,
        title="Organization contact information",
        description="Contact for the organization",
        json_schema_extra={"nskey": "schema"},
    )
    schemaKey: Literal["Organization"] = Field(
        "Organization", validate_default=True, json_schema_extra={"readOnly": True}
    )
    _ldmeta = {
        "rdfs:subClassOf": ["schema:Organization", "prov:Organization"],
        "nskey": DANDI_NSKEY,
    }


class Affiliation(DandiBaseModel):
    identifier: Optional[RORID] = Field(
        None,
        title="A ror.org identifier",
        description="Use an ror.org identifier for institutions.",
        pattern=r"^https://ror.org/[a-z0-9]+$",
        json_schema_extra={"nskey": "schema"},
    )
    name: str = Field(
        json_schema_extra={"nskey": "schema"}, description="Name of organization"
    )
    schemaKey: Literal["Affiliation"] = Field(
        "Affiliation", validate_default=True, json_schema_extra={"readOnly": True}
    )

    _ldmeta = {
        "rdfs:subClassOf": ["schema:Organization", "prov:Organization"],
        "nskey": DANDI_NSKEY,
    }


class Person(Contributor):
    identifier: Optional[ORCID] = Field(
        None,
        title="An ORCID identifier",
        description="An ORCID (orcid.org) identifier for an individual.",
        pattern=r"^\d{4}-\d{4}-\d{4}-(\d{3}X|\d{4})$",
        json_schema_extra={"nskey": "schema"},
    )
    name: str = Field(
        title="Use Last, First. Example: Lovelace, Augusta Ada",
        description="Use the format: familyname, given names ...",
        pattern=NAME_PATTERN,
        json_schema_extra={"nskey": "schema"},
    )
    affiliation: Optional[List[Affiliation]] = Field(
        None,
        description="An organization that this person is affiliated with.",
        json_schema_extra={"nskey": "schema"},
    )
    schemaKey: Literal["Person"] = Field(
        "Person", validate_default=True, json_schema_extra={"readOnly": True}
    )

    _ldmeta = {
        "rdfs:subClassOf": ["schema:Person", "prov:Person"],
        "nskey": DANDI_NSKEY,
    }


class Software(DandiBaseModel):
    identifier: Optional[RRID] = Field(
        None,
        pattern=r"^RRID:.*",
        title="Research resource identifier",
        description="RRID of the software from scicrunch.org.",
        json_schema_extra={"nskey": "schema"},
    )
    name: str = Field(json_schema_extra={"nskey": "schema"})
    version: str = Field(json_schema_extra={"nskey": "schema"})
    url: Optional[AnyHttpUrl] = Field(
        None,
        description="Web page for the software.",
        json_schema_extra={"nskey": "schema"},
    )
    schemaKey: Literal["Software"] = Field(
        "Software", validate_default=True, json_schema_extra={"readOnly": True}
    )

    _ldmeta = {
        "rdfs:subClassOf": ["schema:SoftwareApplication", "prov:Software"],
        "nskey": DANDI_NSKEY,
    }


class Agent(DandiBaseModel):
    identifier: Optional[Identifier] = Field(
        None,
        title="Identifier",
        description="Identifier for an agent.",
        json_schema_extra={"nskey": "schema"},
    )
    name: str = Field(
        json_schema_extra={"nskey": "schema"},
    )
    url: Optional[AnyHttpUrl] = Field(None, json_schema_extra={"nskey": "schema"})
    schemaKey: Literal["Agent"] = Field(
        "Agent", validate_default=True, json_schema_extra={"readOnly": True}
    )

    _ldmeta = {
        "rdfs:subClassOf": ["prov:Agent"],
        "nskey": DANDI_NSKEY,
    }


class EthicsApproval(DandiBaseModel):
    """Information about ethics committee approval for project"""

    identifier: Identifier = Field(
        json_schema_extra={"nskey": "schema"},
        title="Approved protocol identifier",
        description="Approved Protocol identifier, often a number or alphanumeric string.",
    )
    contactPoint: Optional[ContactPoint] = Field(
        None,
        description="Information about the ethics approval committee.",
        json_schema_extra={"nskey": "schema"},
    )
    schemaKey: Literal["EthicsApproval"] = Field(
        "EthicsApproval", validate_default=True, json_schema_extra={"readOnly": True}
    )

    _ldmeta = {"rdfs:subClassOf": ["schema:Thing", "prov:Entity"], "nskey": DANDI_NSKEY}


class Resource(DandiBaseModel):
    identifier: Optional[Identifier] = Field(
        None, json_schema_extra={"nskey": "schema"}
    )
    name: Optional[str] = Field(
        None, title="A title of the resource", json_schema_extra={"nskey": "schema"}
    )
    url: Optional[AnyHttpUrl] = Field(
        None, title="URL of the resource", json_schema_extra={"nskey": "schema"}
    )
    repository: Optional[str] = Field(
        None,
        title="Name of the repository",
        description="Name of the repository in which the resource is housed.",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    relation: RelationType = Field(
        title="Resource relation",
        description="Indicates how the resource is related to the dataset. "
        "This relation should satisfy: dandiset <relation> resource.",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    resourceType: Optional[ResourceType] = Field(
        default=None,
        title="Resource type",
        description="The type of resource.",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )

    schemaKey: Literal["Resource"] = Field(
        "Resource", validate_default=True, json_schema_extra={"readOnly": True}
    )

    _ldmeta = {
        "rdfs:subClassOf": ["schema:CreativeWork", "prov:Entity"],
        "rdfs:comment": "A resource related to the project (e.g., another "
        "dataset, publication, Webpage)",
        "nskey": DANDI_NSKEY,
    }

    @model_validator(mode="after")
    def identifier_or_url(self) -> "Resource":
        identifier, url = self.identifier, self.url
        if identifier is None and url is None:
            raise ValueError("Both identifier and url cannot be None")
        return self


class AccessRequirements(DandiBaseModel):
    """Information about access options for the dataset"""

    status: AccessType = Field(
        title="Access status",
        description="The access status of the item.",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    contactPoint: Optional[ContactPoint] = Field(
        None,
        description="Who or where to look for information about access.",
        json_schema_extra={"nskey": "schema"},
    )
    description: Optional[str] = Field(
        None,
        description="Information about access requirements when embargoed or restricted",
        json_schema_extra={"nskey": "schema"},
    )
    embargoedUntil: Optional[date] = Field(
        None,
        title="Embargo end date",
        description="Date on which embargo ends.",
        json_schema_extra={
            "readOnly": True,
            "nskey": DANDI_NSKEY,
            "rangeIncludes": "schema:Date",
        },
    )
    schemaKey: Literal["AccessRequirements"] = Field(
        "AccessRequirements",
        validate_default=True,
        json_schema_extra={"readOnly": True},
    )

    _ldmeta = {"rdfs:subClassOf": ["schema:Thing", "prov:Entity"], "nskey": DANDI_NSKEY}

    @model_validator(mode="after")
    def open_or_embargoed(self) -> "AccessRequirements":
        status, embargoed = self.status, self.embargoedUntil
        if status == AccessType.EmbargoedAccess and embargoed is None:
            raise ValueError(
                "An embargo end date is required for NIH awards to be in "
                "compliance with NIH resource sharing policy."
            )
        return self


class AssetsSummary(DandiBaseModel):
    """Summary over assets contained in a dandiset (published or not)"""

    # stats which are not stats
    numberOfBytes: int = Field(
        json_schema_extra={"readOnly": True, "sameas": "schema:contentSize"}
    )
    numberOfFiles: int = Field(json_schema_extra={"readOnly": True})  # universe
    numberOfSubjects: Optional[int] = Field(
        None, json_schema_extra={"readOnly": True}
    )  # NWB + BIDS
    numberOfSamples: Optional[int] = Field(
        None, json_schema_extra={"readOnly": True}
    )  # more of NWB
    numberOfCells: Optional[int] = Field(None, json_schema_extra={"readOnly": True})

    dataStandard: Optional[List[StandardsType]] = Field(
        None, json_schema_extra={"readOnly": True}
    )
    # Web UI: icons per each modality?
    approach: Optional[List[ApproachType]] = Field(
        None, json_schema_extra={"readOnly": True}
    )
    # Web UI: could be an icon with number, which if hovered on  show a list?
    measurementTechnique: Optional[List[MeasurementTechniqueType]] = Field(
        None, json_schema_extra={"readOnly": True, "nskey": "schema"}
    )
    variableMeasured: Optional[List[str]] = Field(
        None, json_schema_extra={"readOnly": True, "nskey": "schema"}
    )

    species: Optional[List[SpeciesType]] = Field(
        None, json_schema_extra={"readOnly": True}
    )
    schemaKey: Literal["AssetsSummary"] = Field(
        "AssetsSummary", validate_default=True, json_schema_extra={"readOnly": True}
    )

    _ldmeta = {
        "rdfs:subClassOf": ["schema:CreativeWork", "prov:Entity"],
        "nskey": DANDI_NSKEY,
    }


class Equipment(DandiBaseModel):
    identifier: Optional[Identifier] = Field(
        None, json_schema_extra={"nskey": "schema"}
    )
    name: str = Field(
        title="Title",
        description="A name for the equipment.",
        max_length=150,
        json_schema_extra={"nskey": "schema"},
    )
    description: Optional[str] = Field(
        None,
        description="The description of the equipment.",
        json_schema_extra={"nskey": "schema"},
    )
    schemaKey: Literal["Equipment"] = Field(
        "Equipment", validate_default=True, json_schema_extra={"readOnly": True}
    )

    _ldmeta = {
        "rdfs:subClassOf": ["schema:CreativeWork", "prov:Entity"],
        "nskey": DANDI_NSKEY,
    }


class Activity(DandiBaseModel):
    """Information about the Project activity"""

    identifier: Optional[Identifier] = Field(
        None, json_schema_extra={"nskey": "schema"}
    )
    name: str = Field(
        title="Title",
        description="The name of the activity.",
        max_length=150,
        json_schema_extra={"nskey": "schema"},
    )
    description: Optional[str] = Field(
        None,
        description="The description of the activity.",
        json_schema_extra={"nskey": "schema"},
    )
    startDate: Optional[datetime] = Field(None, json_schema_extra={"nskey": "schema"})
    endDate: Optional[datetime] = Field(None, json_schema_extra={"nskey": "schema"})

    # isPartOf: Optional["Activity"] = Field(None, json_schema_extra={"nskey": "schema"})
    # hasPart: Optional["Activity"] = Field(None, json_schema_extra={"nskey": "schema"})
    wasAssociatedWith: Optional[
        List[
            Annotated[
                Union[Person, Organization, Software, Agent],
                Field(discriminator="schemaKey"),
            ]
        ]
    ] = Field(None, json_schema_extra={"nskey": "prov"})
    used: Optional[List[Equipment]] = Field(
        None,
        description="A listing of equipment used for the activity.",
        json_schema_extra={"nskey": "prov"},
    )
    schemaKey: Literal["Activity", "Project", "Session", "PublishActivity"] = Field(
        "Activity", validate_default=True, json_schema_extra={"readOnly": True}
    )

    _ldmeta = {
        "rdfs:subClassOf": ["prov:Activity", "schema:Thing"],
        "nskey": DANDI_NSKEY,
    }


class Project(Activity):
    name: str = Field(
        title="Name of project",
        description="The name of the project that generated this Dandiset or asset.",
        max_length=150,
        json_schema_extra={"nskey": "schema"},
    )
    description: Optional[str] = Field(
        None,
        description="A brief description of the project.",
        json_schema_extra={"nskey": "schema"},
    )
    schemaKey: Literal["Project"] = Field(
        "Project", validate_default=True, json_schema_extra={"readOnly": True}
    )


class Session(Activity):
    name: str = Field(
        title="Name of session",
        description="The name of the logical session associated with the asset.",
        max_length=150,
        json_schema_extra={"nskey": "schema"},
    )
    description: Optional[str] = Field(
        None,
        description="A brief description of the session.",
        json_schema_extra={"nskey": "schema"},
    )
    schemaKey: Literal["Session"] = Field(
        "Session", validate_default=True, json_schema_extra={"readOnly": True}
    )


class PublishActivity(Activity):
    schemaKey: Literal["PublishActivity"] = Field(
        "PublishActivity", validate_default=True, json_schema_extra={"readOnly": True}
    )


class Locus(DandiBaseModel):
    identifier: Union[Identifier, List[Identifier]] = Field(
        description="Identifier for genotyping locus.",
        json_schema_extra={"nskey": "schema"},
    )
    locusType: Optional[str] = Field(None)
    schemaKey: Literal["Locus"] = Field(
        "Locus", validate_default=True, json_schema_extra={"readOnly": True}
    )
    _ldmeta = {"nskey": DANDI_NSKEY}


class Allele(DandiBaseModel):
    identifier: Union[Identifier, List[Identifier]] = Field(
        description="Identifier for genotyping allele.",
        json_schema_extra={"nskey": "schema"},
    )
    alleleSymbol: Optional[str] = Field(None)
    alleleType: Optional[str] = Field(None)
    schemaKey: Literal["Allele"] = Field(
        "Allele", validate_default=True, json_schema_extra={"readOnly": True}
    )
    _ldmeta = {"nskey": DANDI_NSKEY}


class GenotypeInfo(DandiBaseModel):
    locus: Locus = Field(description="Locus at which information was extracted.")
    alleles: List[Allele] = Field(description="Information about alleles at the locus.")
    wasGeneratedBy: Optional[List["Session"]] = Field(
        None,
        description="Information about session activity used to determine genotype.",
        json_schema_extra={"nskey": "prov"},
    )
    schemaKey: Literal["GenotypeInfo"] = Field(
        "GenotypeInfo", validate_default=True, json_schema_extra={"readOnly": True}
    )
    _ldmeta = {"nskey": DANDI_NSKEY}


class RelatedParticipant(DandiBaseModel):
    identifier: Optional[Identifier] = Field(
        None, json_schema_extra={"nskey": "schema"}
    )
    name: Optional[str] = Field(
        None,
        title="Name of the participant or subject",
        json_schema_extra={"nskey": "schema"},
    )
    url: Optional[AnyHttpUrl] = Field(
        None,
        title="URL of the related participant or subject",
        json_schema_extra={"nskey": "schema"},
    )
    relation: ParticipantRelationType = Field(
        title="Participant or subject relation",
        description="Indicates how the current participant or subject is related "
        "to the other participant or subject. This relation should "
        "satisfy: Participant/Subject <relation> relatedParticipant/Subject.",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    schemaKey: Literal["RelatedParticipant"] = Field(
        "RelatedParticipant",
        validate_default=True,
        json_schema_extra={"readOnly": True},
    )

    _ldmeta = {
        "rdfs:subClassOf": ["schema:CreativeWork", "prov:Entity"],
        "rdfs:comment": "Another participant or subject related to the current "
        "participant or subject (e.g., another parent, sibling, child).",
        "nskey": DANDI_NSKEY,
    }


class Participant(DandiBaseModel):
    """Description about the Participant or Subject studied.

    The Participant or Subject can be any individual or synthesized Agent. The
    properties of the Participant or Subject refers to information at the timepoint
    when the Participant or Subject engaged in the production of data being described.
    """

    identifier: Identifier = Field(json_schema_extra={"nskey": "schema"})
    altName: Optional[List[Identifier]] = Field(
        None, json_schema_extra={"nskey": DANDI_NSKEY}
    )

    strain: Optional[StrainType] = Field(
        None,
        description="Identifier for the strain of the participant or subject.",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    cellLine: Optional[Identifier] = Field(
        None,
        description="Cell line associated with the participant or subject.",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    vendor: Optional[Organization] = Field(
        None, json_schema_extra={"nskey": DANDI_NSKEY}
    )
    age: Optional[PropertyValue] = Field(
        None,
        description="A representation of age using ISO 8601 duration. This "
        "should include a valueReference if anything other than "
        "date of birth is used.",
        json_schema_extra={"nskey": DANDI_NSKEY, "rangeIncludes": "schema:Duration"},
    )

    sex: Optional[SexType] = Field(
        None,
        description="Identifier for sex of the participant or subject if "
        "available. (e.g. from OBI)",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    genotype: Optional[Union[List[GenotypeInfo], Identifier]] = Field(
        None,
        description="Genotype descriptor of participant or subject if available",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    species: Optional[SpeciesType] = Field(
        None,
        description="An identifier indicating the taxonomic classification of "
        "the participant or subject.",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    disorder: Optional[List[Disorder]] = Field(
        None,
        description="Any current diagnosed disease or disorder associated with "
        "the participant or subject.",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )

    relatedParticipant: Optional[List[RelatedParticipant]] = Field(
        None,
        description="Information about related participants or subjects in a "
        "study or across studies.",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    sameAs: Optional[List[Identifier]] = Field(
        None,
        description="An identifier to link participants or subjects across datasets.",
        json_schema_extra={"nskey": "schema"},
    )
    schemaKey: Literal["Participant"] = Field(
        "Participant", validate_default=True, json_schema_extra={"readOnly": True}
    )

    _ldmeta = {
        "rdfs:subClassOf": ["prov:Agent"],
        "rdfs:label": "Information about the participant or subject.",
        "nskey": DANDI_NSKEY,
    }


class BioSample(DandiBaseModel):
    """Description of the sample that was studied"""

    identifier: Identifier = Field(json_schema_extra={"nskey": "schema"})
    sampleType: SampleType = Field(
        description="Identifier for the sample characteristics (e.g., from OBI, Encode).",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    assayType: Optional[List[AssayType]] = Field(
        None,
        description="Identifier for the assay(s) used (e.g., OBI).",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    anatomy: Optional[List[Anatomy]] = Field(
        None,
        description="Identifier for what organ the sample belongs "
        "to. Use the most specific descriptor from sources such as UBERON.",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )

    wasDerivedFrom: Optional[List["BioSample"]] = Field(
        None,
        description="Describes the hierarchy of sample derivation or aggregation.",
        json_schema_extra={"nskey": "prov"},
    )
    wasAttributedTo: Optional[List[Participant]] = Field(
        None,
        description="Participant(s) or Subject(s) associated with this sample.",
        json_schema_extra={"nskey": "prov"},
    )
    sameAs: Optional[List[Identifier]] = Field(
        None, json_schema_extra={"nskey": "schema"}
    )
    hasMember: Optional[List[Identifier]] = Field(
        None, json_schema_extra={"nskey": "prov"}
    )
    schemaKey: Literal["BioSample"] = Field(
        "BioSample", validate_default=True, json_schema_extra={"readOnly": True}
    )

    _ldmeta = {
        "rdfs:subClassOf": ["schema:Thing", "prov:Entity"],
        "rdfs:label": "Information about the biosample.",
        "nskey": DANDI_NSKEY,
    }


# This is mostly not needed at all since self-referencing models
# are automatically resolved by Pydantic in a pretty consistent way even in Pydantic V1
# https://docs.pydantic.dev/1.10/usage/postponed_annotations/#self-referencing-models
# and continue to be so in Pydantic V2
# https://docs.pydantic.dev/latest/concepts/postponed_annotations/#self-referencing-or-recursive-models
BioSample.model_rebuild()


def repository_default() -> AnyHttpUrl | None:
    url = get_instance_config().dandi_instance_url
    if url is not None:
        return TypeAdapter(AnyHttpUrl).validate_python(url)

    return None


class CommonModel(DandiBaseModel):
    schemaVersion: str = Field(
        default=DANDI_SCHEMA_VERSION,
        json_schema_extra={"readOnly": True, "nskey": "schema"},
    )
    name: Optional[str] = Field(
        None,
        title="Title",
        description="The name of the item.",
        max_length=150,
        json_schema_extra={"nskey": "schema"},
    )
    description: Optional[str] = Field(
        None,
        description="A description of the item.",
        json_schema_extra={"nskey": "schema"},
    )
    contributor: Optional[
        List[Annotated[Union[Person, Organization], Field(discriminator="schemaKey")]]
    ] = Field(
        None,
        title="Contributors",
        description="Contributors to this item: persons or organizations.",
        json_schema_extra={"nskey": "schema"},
    )
    about: Optional[
        List[
            Annotated[
                Union[Disorder, Anatomy, GenericType], Field(discriminator="schemaKey")
            ]
        ]
    ] = Field(
        None,
        title="Subject matter of the dataset",
        description="The subject matter of the content, such as disorders, brain anatomy.",
        json_schema_extra={"nskey": "schema"},
    )
    studyTarget: Optional[List[str]] = Field(
        None,
        description="Objectives or specific questions of the study.",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    license: Optional[List[LicenseType]] = Field(
        None,
        description="Licenses associated with the item. DANDI only supports a "
        "subset of Creative Commons Licenses (creativecommons.org) "
        "applicable to datasets.",
        json_schema_extra={"nskey": "schema"},
    )
    protocol: Optional[List[AnyHttpUrl]] = Field(
        None,
        description="A list of persistent URLs describing the protocol (e.g. "
        "protocols.io, or other DOIs).",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    ethicsApproval: Optional[List[EthicsApproval]] = Field(
        None, title="Ethics approvals", json_schema_extra={"nskey": DANDI_NSKEY}
    )
    keywords: Optional[List[str]] = Field(
        None,
        description="Keywords used to describe this content.",
        json_schema_extra={"nskey": "schema"},
    )
    acknowledgement: Optional[str] = Field(
        None,
        description="Any acknowledgments not covered by contributors or external resources.",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )

    # Linking to this dandiset or the larger thing
    access: List[AccessRequirements] = Field(
        title="Access information",
        default_factory=lambda: [AccessRequirements(status=AccessType.OpenAccess)],
        json_schema_extra={"nskey": DANDI_NSKEY, "readOnly": True},
    )
    url: Optional[AnyHttpUrl] = Field(
        None,
        description="permalink to the item",
        json_schema_extra={"readOnly": True, "nskey": "schema"},
    )
    repository: Optional[AnyHttpUrl] = Field(
        # mypy doesn't like using a string as the default for an AnyHttpUrl
        # attribute, so we have to convert it to an AnyHttpUrl:
        default_factory=repository_default,
        description="location of the item",
        json_schema_extra={"nskey": DANDI_NSKEY, "readOnly": True},
    )
    relatedResource: Optional[List[Resource]] = Field(
        None, json_schema_extra={"nskey": DANDI_NSKEY}
    )

    wasGeneratedBy: Optional[Sequence[Activity]] = Field(
        None, json_schema_extra={"nskey": "prov"}
    )
    schemaKey: str = Field(
        "CommonModel", validate_default=True, json_schema_extra={"readOnly": True}
    )


class Dandiset(CommonModel):
    """A body of structured information describing a DANDI dataset."""

    model_config = ConfigDict(extra="allow")

    @field_validator("contributor")
    @classmethod
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

    @field_validator("id")
    @staticmethod
    def check_id(value: str) -> str:
        conf = get_instance_config()
        sub_pattern = conf.id_pattern + "|" + conf.id_pattern.lower()
        pattern = rf"^({sub_pattern}):\d{{6}}(/(draft|\d+\.\d+\.\d+))$"

        if re.match(pattern, value) is None:
            raise ValueError("ID does not match pattern")

        return value

    @field_validator("identifier")
    @staticmethod
    def check_identifier(value: str) -> str:
        conf = get_instance_config()
        pattern = rf"^{conf.id_pattern}:\d{{6}}$"

        if re.match(pattern, value) is None:
            raise ValueError("Identifier does not match pattern")

        return value

    id: str = Field(
        description="Uniform resource identifier",
        json_schema_extra={"readOnly": True},
    )

    identifier: DANDI = Field(
        title="Dandiset identifier",
        description="A Dandiset identifier that can be resolved by identifiers.org.",
        json_schema_extra={"readOnly": True, "nskey": "schema"},
    )
    name: str = Field(
        title="Dandiset title",
        description="A title associated with the Dandiset.",
        max_length=150,
        json_schema_extra={"nskey": "schema"},
    )
    description: str = Field(
        description="A description of the Dandiset",
        max_length=10000,
        json_schema_extra={"nskey": "schema"},
    )
    contributor: List[
        Annotated[Union[Person, Organization], Field(discriminator="schemaKey")]
    ] = Field(
        title="Dandiset contributors",
        description="People or Organizations that have contributed to this Dandiset.",
        json_schema_extra={"nskey": "schema"},
        min_length=1,
    )
    dateCreated: Optional[datetime] = Field(
        None,
        json_schema_extra={"nskey": "schema", "readOnly": True},
        title="Dandiset creation date and time.",
    )
    dateModified: Optional[datetime] = Field(
        None,
        json_schema_extra={"nskey": "schema", "readOnly": True},
        title="Last modification date and time.",
    )

    license: List[LicenseType] = Field(
        min_length=1,
        description="Licenses associated with the item. DANDI only supports a "
        "subset of Creative Commons Licenses (creativecommons.org) "
        "applicable to datasets.",
        json_schema_extra={"nskey": "schema"},
    )

    citation: str = Field(json_schema_extra={"readOnly": True, "nskey": "schema"})

    # From assets
    assetsSummary: AssetsSummary = Field(
        json_schema_extra={"nskey": DANDI_NSKEY, "readOnly": True}
    )

    # From server (requested by users even for drafts)
    manifestLocation: List[AnyHttpUrl] = Field(
        min_length=1, json_schema_extra={"nskey": DANDI_NSKEY, "readOnly": True}
    )

    version: str = Field(json_schema_extra={"nskey": "schema", "readOnly": True})

    wasGeneratedBy: Optional[Sequence[Project]] = Field(
        None,
        title="Associated projects",
        description="Project(s) that generated this Dandiset.",
        json_schema_extra={"nskey": "prov"},
    )

    schemaKey: Literal["Dandiset"] = Field(
        "Dandiset", validate_default=True, json_schema_extra={"readOnly": True}
    )

    _ldmeta = {
        "rdfs:subClassOf": ["schema:Dataset", "prov:Entity"],
        "rdfs:label": "Information about the dataset",
        "nskey": DANDI_NSKEY,
    }


class BareAsset(CommonModel):
    """Metadata used to describe an asset anywhere (local or server).

    Derived from C2M2 (Level 0 and 1) and schema.org
    """

    contentSize: ByteSizeJsonSchema = Field(json_schema_extra={"nskey": "schema"})
    encodingFormat: Union[AnyHttpUrl, str] = Field(
        title="File encoding format", json_schema_extra={"nskey": "schema"}
    )
    digest: Dict[DigestType, str] = Field(
        title="A map of dandi digests to their values",
        json_schema_extra={"nskey": DANDI_NSKEY},
    )
    path: str = Field(json_schema_extra={"nskey": DANDI_NSKEY})

    dateModified: Optional[datetime] = Field(
        None,
        json_schema_extra={"nskey": "schema"},
        title="Asset (file or metadata) modification date and time",
    )
    blobDateModified: Optional[datetime] = Field(
        None,
        json_schema_extra={"nskey": DANDI_NSKEY},
        title="Asset file modification date and time.",
    )
    # overload to restrict with max_items=1
    access: List[AccessRequirements] = Field(
        title="Access information",
        default_factory=lambda: [AccessRequirements(status=AccessType.OpenAccess)],
        json_schema_extra={"nskey": DANDI_NSKEY},
        max_length=1,
    )

    # this is from C2M2 level 1 - using EDAM vocabularies - in our case we would
    # need to come up with things for neurophys
    # TODO: waiting on input <https://github.com/dandi/dandi-cli/pull/226>
    dataType: Optional[AnyHttpUrl] = Field(
        None, json_schema_extra={"nskey": DANDI_NSKEY}
    )

    sameAs: Optional[List[AnyHttpUrl]] = Field(
        None, json_schema_extra={"nskey": "schema"}
    )

    # TODO
    approach: Optional[List[ApproachType]] = Field(
        None, json_schema_extra={"readOnly": True, "nskey": DANDI_NSKEY}
    )
    measurementTechnique: Optional[List[MeasurementTechniqueType]] = Field(
        None, json_schema_extra={"readOnly": True, "nskey": "schema"}
    )
    variableMeasured: Optional[List[PropertyValue]] = Field(
        None, json_schema_extra={"readOnly": True, "nskey": "schema"}
    )

    wasDerivedFrom: Optional[List[BioSample]] = Field(
        None, json_schema_extra={"nskey": "prov"}
    )
    wasAttributedTo: Optional[List[Participant]] = Field(
        None,
        description="Associated participant(s) or subject(s).",
        json_schema_extra={"nskey": "prov"},
    )
    wasGeneratedBy: Optional[List[Union[Session, Project, Activity]]] = Field(
        None,
        title="Name of the session, project or activity.",
        description="Describe the session, project or activity that generated this asset.",
        json_schema_extra={"nskey": "prov"},
    )

    # Bare asset is to be just Asset.
    schemaKey: Literal["Asset"] = Field(
        "Asset", validate_default=True, json_schema_extra={"readOnly": True}
    )

    _ldmeta = {
        "rdfs:subClassOf": ["schema:CreativeWork", "prov:Entity"],
        "rdfs:label": "Information about the asset",
        "nskey": DANDI_NSKEY,
    }

    @field_validator("digest")
    @classmethod
    def digest_check(
        cls, v: Dict[DigestType, str], info: ValidationInfo
    ) -> Dict[DigestType, str]:
        values = info.data
        if values.get("encodingFormat") == "application/x-zarr":
            if DigestType.dandi_zarr_checksum not in v:
                raise ValueError("A zarr asset must have a zarr checksum.")
            if v.get(DigestType.dandi_etag):
                raise ValueError("Digest cannot have both etag and zarr checksums.")
            digest = v[DigestType.dandi_zarr_checksum]
            try:
                chksum = ZarrDirectoryDigest.parse(digest)
            except InvalidZarrChecksum:
                raise ValueError(
                    "Digest must have an appropriate dandi-zarr-checksum value."
                    f"  Got {digest}"
                )
            zarr_size = chksum.size
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
                    f"Digest must have an appropriate dandi-etag value. Got {digest}"
                )
        return v


class Asset(BareAsset):
    """Metadata used to describe an asset on the server."""

    # all of the following are set by server
    id: str = Field(
        json_schema_extra={"readOnly": True}, description="Uniform resource identifier."
    )
    identifier: UUID4 = Field(json_schema_extra={"readOnly": True, "nskey": "schema"})
    contentUrl: List[AnyHttpUrl] = Field(
        json_schema_extra={"readOnly": True, "nskey": "schema"}
    )


class Publishable(DandiBaseModel):
    publishedBy: Union[AnyHttpUrl, PublishActivity] = Field(
        description="The URL should contain the provenance of the publishing process.",
        json_schema_extra={"readOnly": True, "nskey": DANDI_NSKEY},
    )
    datePublished: datetime = Field(
        json_schema_extra={"readOnly": True, "nskey": "schema"}
    )
    schemaKey: Literal["Publishable", "Dandiset", "Asset"] = Field(
        "Publishable", validate_default=True, json_schema_extra={"readOnly": True}
    )


# TODO: Reconcile
# _doi_field_kwargs: dict[str, Any] = {
#     "title": "DOI",
#     "pattern": DANDI_DOI_PATTERN,
#     "json_schema_extra": {"readOnly": True, "nskey": DANDI_NSKEY},
# }
# if _INSTANCE_CONFIG.doi_prefix is None:
#     _doi_field_kwargs["default"] = ""


class PublishedDandiset(Dandiset, Publishable):
    id: str = Field(
        description="Uniform resource identifier.",
        json_schema_extra={"readOnly": True},
    )
    doi: str = Field(
        title="DOI",
        json_schema_extra={"readOnly": True, "nskey": DANDI_NSKEY},
        default="",
    )
    """
    The DOI of the published Dandiset

    The value of the empty string indicates that there is no DOI for the published
    Dandiset.
    """

    url: AnyHttpUrl = Field(
        description="Permalink to the Dandiset.",
        json_schema_extra={"readOnly": True, "nskey": "schema"},
    )

    schemaKey: Literal["Dandiset"] = Field(
        "Dandiset", validate_default=True, json_schema_extra={"readOnly": True}
    )

    @field_validator("assetsSummary")
    @classmethod
    def check_filesbytes(cls, values: AssetsSummary) -> AssetsSummary:
        if values.numberOfBytes == 0 or values.numberOfFiles == 0:
            raise ValueError(
                "A Dandiset containing no files or zero bytes is not publishable"
            )
        return values

    @field_validator("url")
    @classmethod
    def check_url(cls, url: AnyHttpUrl) -> AnyHttpUrl:
        pattern = get_instance_config().published_version_pattern
        if not re.match(pattern, str(url)):
            raise ValueError(f'string does not match regex "{pattern}"')
        return url

    @field_validator("id")
    @staticmethod
    def check_id(idstr: str) -> str:
        pattern = get_instance_config().dandi_pubid_pattern
        if not re.match(pattern, idstr):
            raise ValueError(f'string does not match regex "{pattern}"')

        return idstr

    @field_validator("doi")
    @staticmethod
    def check_doi(doi: str) -> str:
        pattern = get_instance_config().dandi_doi_pattern or r"^$"
        if not re.match(pattern, doi):
            raise ValueError(f'string does not match regex "{pattern}"')

        return doi


class PublishedAsset(Asset, Publishable):
    id: str = Field(
        description="Uniform resource identifier.",
        pattern=ASSET_UUID_PATTERN,
        json_schema_extra={"readOnly": True},
    )

    schemaKey: Literal["Asset"] = Field(
        "Asset", validate_default=True, json_schema_extra={"readOnly": True}
    )

    @field_validator("digest")
    @classmethod
    def digest_sha256check(
        cls, v: Dict[DigestType, str], info: ValidationInfo
    ) -> Dict[DigestType, str]:
        values = info.data
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
