from copy import deepcopy
from datetime import date, datetime
from enum import Enum
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import (
    UUID4,
    AnyHttpUrl,
    BaseModel,
    ByteSize,
    EmailStr,
    Field,
    HttpUrl,
    root_validator,
    validator,
)
from pydantic.main import ModelMetaclass

from .consts import DANDI_SCHEMA_VERSION
from .model_types import (
    AccessTypeDict,
    AgeReferenceTypeDict,
    DigestTypeDict,
    IdentifierTypeDict,
    LicenseTypeDict,
    ParticipantRelationTypeDict,
    RelationTypeDict,
    RoleTypeDict,
)
from .utils import name2title

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

# Local or test deployments of dandi-api will insert URLs into the schema that refer to the domain
# localhost, which is not a valid TLD. To make the metadata valid in those contexts, setting this
# environment variable will use a less restrictive pydantic field that allows localhost.
if "DANDI_ALLOW_LOCALHOST_URLS" in os.environ:
    HttpUrl = AnyHttpUrl  # noqa: F811


NAME_PATTERN = r"^([\w\s\-]+)?,\s+([\w\s\-\.]+)?$"
UUID_PATTERN = (
    "[a-f0-9]{8}[-]*[a-f0-9]{4}[-]*" "[a-f0-9]{4}[-]*[a-f0-9]{4}[-]*[a-f0-9]{12}$"
)
ASSET_UUID_PATTERN = r"^dandiasset:" + UUID_PATTERN
DANDI_DOI_PATTERN = r"^10.(48324|80507)/dandi\.\d{6}/\d+\.\d+\.\d+"
DANDI_PUBID_PATTERN = r"^DANDI:\d{6}/\d+\.\d+\.\d+"


def create_enum(data):
    """Convert a JSON-LD enumeration to an Enum"""
    items = {}
    klass = None
    for idx, item in enumerate(data["@graph"]):
        if item["@type"] == "rdfs:Class":
            klass = item["@id"].replace("dandi:", "")
            klass_doc = item["rdfs:comment"]
        else:
            key = item["@id"]
            if ":" in item["@id"]:
                key = item["@id"].split(":")[-1]
            if key in items:
                key = item["@id"].replace(":", "_")
            items[key.replace("-", "_").replace(".", "")] = item["@id"]
    if klass is None or len(items) == 0:
        raise ValueError(f"Could not generate a klass or items from {data}")
    newklass = Enum(klass, items)
    newklass.__doc__ = klass_doc
    return newklass


def split_name(name):
    space_added = []
    for c in name:
        if c.upper() == c:
            space_added.append(" ")
        space_added.append(c)
    labels = "".join(space_added).split()
    labels[0] = labels[0].capitalize()
    for idx in range(1, len(labels)):
        labels[idx] = labels[idx].lower()
    return " ".join(labels)


if len(AccessTypeDict["@graph"]) > 2:
    AccessTypeDict["@graph"].pop()
    AccessTypeDict["@graph"].pop()
AccessType = create_enum(AccessTypeDict)
AgeReferenceType = create_enum(AgeReferenceTypeDict)
RoleType = create_enum(RoleTypeDict)
RelationType = create_enum(RelationTypeDict)
ParticipantRelationType = create_enum(ParticipantRelationTypeDict)
LicenseType = create_enum(LicenseTypeDict)
IdentifierType = create_enum(IdentifierTypeDict)
DigestType = create_enum(DigestTypeDict)


def diff_models(model1, model2):
    """Perform a field-wise diff"""
    for field in model1.__fields__:
        if getattr(model1, field) != getattr(model2, field):
            print(f"{field} is different")


def _sanitize(o):
    if isinstance(o, dict):
        return {_sanitize(k): _sanitize(v) for k, v in o.items()}
    elif isinstance(o, (set, tuple, list)):
        return type(o)(_sanitize(x) for x in o)
    elif isinstance(o, Enum):
        return o.value
    return o


class HandleKeyEnumEncoder(json.JSONEncoder):
    def encode(self, o):
        return super().encode(_sanitize(o))


class DandiBaseModelMetaclass(ModelMetaclass):
    def __new__(cls, name, bases, dct):
        sk_name = dct.pop("schemaKey", None) or name
        dct["schemaKey"]: Literal[sk_name] = Field(sk_name, readOnly=True)
        objcls = super().__new__(cls, name, bases, dct)
        return objcls


class DandiBaseModel(BaseModel, metaclass=DandiBaseModelMetaclass):
    id: Optional[str] = Field(description="Uniform resource identifier", readOnly=True)

    def json_dict(self):
        """
        Recursively convert the instance to a `dict` of JSONable values,
        including converting enum values to strings.  `None` fields
        are omitted.
        """
        return json.loads(self.json(exclude_none=True, cls=HandleKeyEnumEncoder))

    @validator("schemaKey", always=True)
    def ensure_schemakey(cls, val):
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
        self = __pydantic_cls__.__new__(__pydantic_cls__)
        object.__setattr__(self, "__dict__", data)
        object.__setattr__(self, "__fields_set__", set(data.keys()))
        return self

    @classmethod
    def to_dictrepr(__pydantic_cls__: Type["DandiBaseModel"]):
        return (
            __pydantic_cls__.unvalidated()
            .__repr__()
            .replace(__pydantic_cls__.__name__, "dict")
        )

    class Config:
        @staticmethod
        def schema_extra(schema: Dict[str, Any], model) -> None:
            if schema["title"] == "PropertyValue":
                schema["required"] = list(
                    set(["value"]).union(schema.get("required", []))
                )
            schema["title"] = name2title(schema["title"])
            if schema["type"] == "object":
                schema["required"] = list(
                    set(schema.get("required", [])).union(["schemaKey"])
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
    propertyID: Optional[Union[IdentifierType, HttpUrl]] = Field(
        None,
        description="A commonly used identifier for"
        "the characteristic represented by the property. "
        "For example, a known prefix like DOI or a full URL.",
        nskey="schema",
    )

    @validator("value", always=True)
    def ensure_value(cls, val):
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
DANDIURL = str


class BaseType(DandiBaseModel):
    """Base class for enumerated types"""

    identifier: Optional[Union[HttpUrl, str]] = Field(
        None,
        description="The identifier can be any url or a compact URI, preferably"
        " supported by identifiers.org.",
        regex=r"^[a-zA-Z0-9]+:[a-zA-Z0-9-/\._]+$",
        nskey="schema",
    )
    name: Optional[str] = Field(
        None, description="The name of the item.", max_length=150, nskey="schema"
    )
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


class SampleType(BaseType):
    """OBI based identifier for the sample type used"""


class Anatomy(BaseType):
    """UBERON or other identifier for anatomical part studied"""


class StrainType(BaseType):
    """Identifier for the strain of the sample"""


class SexType(BaseType):
    """Identifier for the sex of the sample"""


class SpeciesType(BaseType):
    """Identifier for species of the sample"""


class Disorder(BaseType):
    """Biolink, SNOMED, or other identifier for disorder studied"""

    dxdate: Optional[List[Union[date, datetime]]] = Field(
        None,
        title="Dates of diagnosis",
        description="Dates of diagnosis",
        nskey="dandi",
        rangeIncludes="schema:Date",
    )


class GenericType(BaseType):
    """An object to capture any type for about"""


class ApproachType(BaseType):
    """Identifier for approach used"""


class MeasurementTechniqueType(BaseType):
    """Identifier for measurement technique used"""


class StandardsType(BaseType):
    """Identifier for data standard used"""


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
    url: Optional[HttpUrl] = Field(
        None,
        description="A Web page to find information on how to contact.",
        nskey="schema",
    )

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
    url: Optional[HttpUrl] = Field(None, nskey="schema")
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
    url: Optional[HttpUrl] = Field(
        None, description="Web page for the software.", nskey="schema"
    )

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
    url: Optional[HttpUrl] = Field(None, nskey="schema")

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

    _ldmeta = {"rdfs:subClassOf": ["schema:Thing", "prov:Entity"], "nskey": "dandi"}


class Resource(DandiBaseModel):
    identifier: Optional[Identifier] = Field(None, nskey="schema")
    name: Optional[str] = Field(None, title="A title of the resource", nskey="schema")
    url: Optional[HttpUrl] = Field(None, title="URL of the resource", nskey="schema")
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

    _ldmeta = {
        "rdfs:subClassOf": ["schema:CreativeWork", "prov:Entity"],
        "rdfs:comment": "A resource related to the project (e.g., another "
        "dataset, publication, Webpage)",
        "nskey": "dandi",
    }

    @root_validator
    def identifier_or_url(cls, values):
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

    _ldmeta = {"rdfs:subClassOf": ["schema:Thing", "prov:Entity"], "nskey": "dandi"}

    """
    # TODO: Enable when embargoed access is supported.
    @root_validator
    def open_or_embargoed(cls, values):
        status, embargoed = values.get("status"), values.get("embargoedUntil")
        if status == AccessType.EmbargoedAccess and embargoed is None:
            raise ValueError("An embargo date. For NIH supported awards, this "
            "must comply with NIH policy. For other datasets, this will be at "
            "most a year from the dandiset creation.")
        return values
    """


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


class PublishActivity(Activity):
    pass


class Locus(DandiBaseModel):
    identifier: Union[Identifier, List[Identifier]] = Field(
        description="Identifier for genotyping locus.", nskey="schema"
    )
    locusType: Optional[str] = Field(None)
    _ldmeta = {"nskey": "dandi"}


class Allele(DandiBaseModel):
    identifier: Union[Identifier, List[Identifier]] = Field(
        description="Identifier for genotyping allele.", nskey="schema"
    )
    alleleSymbol: Optional[str] = Field(None)
    alleleType: Optional[str] = Field(None)
    _ldmeta = {"nskey": "dandi"}


class GenotypeInfo(DandiBaseModel):
    locus: Locus = Field(description="Locus at which information was extracted.")
    alleles: List[Allele] = Field(description="Information about alleles at the locus.")
    wasGeneratedBy: Optional[List["Session"]] = Field(
        None,
        description="Information about session activity used to determine genotype.",
        nskey="prov",
    )
    _ldmeta = {"nskey": "dandi"}


class RelatedParticipant(DandiBaseModel):
    identifier: Optional[Identifier] = Field(None, nskey="schema")
    name: Optional[str] = Field(
        None, title="Name of the participant or subject", nskey="schema"
    )
    url: Optional[HttpUrl] = Field(
        None, title="URL of the related participant or subject", nskey="schema"
    )
    relation: ParticipantRelationType = Field(
        title="Participant or subject relation",
        description="Indicates how the current participant or subject is related "
        "to the other participant or subject. This relation should "
        "satisfy: Participant/Subject <relation> relatedParticipant/Subject.",
        nskey="dandi",
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
    protocol: Optional[List[HttpUrl]] = Field(
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
    )
    url: Optional[HttpUrl] = Field(
        None, readOnly=True, description="permalink to the item", nskey="schema"
    )
    repository: HttpUrl = Field(
        "https://dandiarchive.org/",
        readOnly=True,
        description="location of the item",
        nskey="dandi",
    )
    relatedResource: Optional[List[Resource]] = Field(None, nskey="dandi")

    wasGeneratedBy: Optional[List[Activity]] = Field(None, nskey="prov")


class Dandiset(CommonModel):
    """A body of structured information describing a DANDI dataset."""

    @validator("contributor")
    def contributor_musthave_contact(cls, values):
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
    manifestLocation: List[HttpUrl] = Field(readOnly=True, min_items=1, nskey="dandi")

    version: str = Field(readOnly=True, nskey="schema")

    wasGeneratedBy: Optional[List[Project]] = Field(
        None,
        title="Associated projects",
        description="Project(s) that generated this Dandiset.",
        nskey="prov",
    )

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
    encodingFormat: Union[HttpUrl, str] = Field(
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
    dataType: Optional[HttpUrl] = Field(None, nskey="dandi")

    sameAs: Optional[List[HttpUrl]] = Field(None, nskey="schema")

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
    schemaKey = "Asset"

    _ldmeta = {
        "rdfs:subClassOf": ["schema:CreativeWork", "prov:Entity"],
        "rdfs:label": "Information about the asset",
        "nskey": "dandi",
    }

    @validator("digest")
    def digest_etag(cls, values):
        try:
            digest = values[DigestType.dandi_etag]
            if "-" not in digest or len(digest.split("-")[0]) != 32:
                raise ValueError
        except KeyError:
            raise ValueError("Digest is missing dandi-etag value.")
        except ValueError:
            raise ValueError(
                f"Digest must have an appropriate dandi-etag value. "
                f"Got {values[DigestType.dandi_etag]}"
            )
        return values


class Asset(BareAsset):
    """Metadata used to describe an asset on the server."""

    # all of the following are set by server
    id: str = Field(readOnly=True, description="Uniform resource identifier.")
    identifier: UUID4 = Field(readOnly=True, nskey="schema")
    contentUrl: List[HttpUrl] = Field(readOnly=True, nskey="schema")


class Publishable(DandiBaseModel):
    publishedBy: Union[HttpUrl, PublishActivity] = Field(
        description="The URL should contain the provenance of the publishing process.",
        readOnly=True,
        nskey="dandi",
    )
    datePublished: datetime = Field(readOnly=True, nskey="schema")


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
    url: DANDIURL = Field(
        readOnly=True,
        description="Permalink to the Dandiset.",
        regex=r"^https://dandiarchive.org/dandiset/\d{6}/\d+\.\d+\.\d+$",
        nskey="schema",
    )

    schemaKey = "Dandiset"

    @validator("assetsSummary")
    def check_filesbytes(cls, values):
        if values.numberOfBytes == 0 or values.numberOfFiles == 0:
            raise ValueError(
                "A Dandiset containing no files or zero bytes is not publishable"
            )
        return values


class PublishedAsset(Asset, Publishable):

    id: str = Field(
        description="Uniform resource identifier.",
        regex=ASSET_UUID_PATTERN,
        readOnly=True,
    )

    schemaKey = "Asset"

    @validator("digest")
    def digest_bothhashes(cls, values):
        try:
            digest = values[DigestType.dandi_etag]
            if "-" not in digest or len(digest.split("-")[0]) != 32:
                raise ValueError("Digest is missing dandi-etag value")
            digest = values[DigestType.sha2_256]
            if len(digest) != 64:
                raise ValueError("Digest is missing sha2_256 value")
        except KeyError:
            raise ValueError("Digest is missing dandi-etag or sha256 keys.")
        return values


def get_schema_version():
    return DANDI_SCHEMA_VERSION
