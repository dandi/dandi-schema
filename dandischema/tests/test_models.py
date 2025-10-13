from collections import namedtuple
from enum import Enum
from inspect import isclass
from typing import Any, Dict, List, Literal, Optional, Tuple, Type, Union, cast

import pydantic
from pydantic import Field, ValidationError
import pytest

from .utils import _basic_publishmeta
from .. import models
from ..models import (
    DANDI_INSTANCE_URL_PATTERN,
    AccessRequirements,
    AccessType,
    Affiliation,
    AgeReferenceType,
    Asset,
    BaseType,
    CommonModel,
    Contributor,
    DandiBaseModel,
    Dandiset,
    DigestType,
    IdentifierType,
    LicenseType,
    Organization,
    ParticipantRelationType,
    Person,
    PropertyValue,
    PublishedDandiset,
    RelationType,
    Resource,
    RoleType,
)
from ..utils import TransitionalGenerateJsonSchema


def test_dandiset() -> None:
    assert Dandiset.model_construct()  # type: ignore[call-arg]


def test_asset() -> None:
    assert Asset.model_construct()  # type: ignore[call-arg]


def test_asset_digest() -> None:
    with pytest.raises(pydantic.ValidationError) as exc:
        models.BareAsset(
            contentSize=100, encodingFormat="nwb", digest={"sha1": ""}, path="/"
        )

    # Assert validation failed at the `digest` attribute because the provided dictionary
    # key is not one of the DigestType enum values.
    assert len(exc.value.errors()) == 1
    err = exc.value.errors()[0]
    assert err["type"] == "enum"
    assert err["loc"] == ("digest", "sha1", "[key]")

    digest = 32 * "a"
    digest_model = {models.DigestType.dandi_etag: digest}
    with pytest.raises(pydantic.ValidationError) as exc:
        models.BareAsset(
            contentSize=100, encodingFormat="nwb", digest=digest_model, path="/"
        )
    assert any(
        [
            "Digest must have an appropriate dandi-etag value." in val
            for val in set([el["msg"] for el in exc.value.errors()])
        ]
    )
    digest = 32 * "a" + "-1"
    digest_model = {models.DigestType.dandi_etag: digest}
    models.BareAsset(
        contentSize=100, encodingFormat="nwb", digest=digest_model, path="/"
    )
    with pytest.raises(pydantic.ValidationError) as exc:
        models.PublishedAsset(  # type: ignore[call-arg]
            contentSize=100,
            encodingFormat="nwb",
            digest={models.DigestType.dandi_etag: digest, "sha1": ""},
            path="/",
        )

    # Assert validation failed at the `digest` attribute because the provided dictionary
    # key is not one of the DigestType enum values.
    assert any(
        err["type"] == "enum" and err["loc"] == ("digest", "sha1", "[key]")
        for err in exc.value.errors()
    )

    digest_model = {
        models.DigestType.dandi_etag: digest,
        models.DigestType.sha2_256: 63 * "a",
    }
    with pytest.raises(pydantic.ValidationError) as exc:
        models.PublishedAsset(  # type: ignore[call-arg]
            contentSize=100, encodingFormat="nwb", digest=digest_model, path="/"
        )
    assert any(
        "Digest must have an appropriate sha2_256 value." in el["msg"]
        for el in exc.value.errors()
    )
    digest_model = {
        models.DigestType.dandi_etag: digest,
        models.DigestType.sha2_256: 64 * "a",
    }
    with pytest.raises(pydantic.ValidationError) as exc:
        models.PublishedAsset(  # type: ignore[call-arg]
            contentSize=100, encodingFormat="nwb", digest=digest_model, path="/"
        )
    assert not any(
        "Digest must have an appropriate dandi-etag value." in el["msg"]
        for el in exc.value.errors()
    )
    digest_model = {
        models.DigestType.dandi_etag: digest,
    }
    with pytest.raises(pydantic.ValidationError) as exc:
        models.PublishedAsset(  # type: ignore[call-arg]
            contentSize=100, encodingFormat="nwb", digest=digest_model, path="/"
        )
    assert any(
        "A non-zarr asset must have a sha2_256." in el["msg"]
        for el in exc.value.errors()
    )

    digest = 32 * "a"
    digest_model = {models.DigestType.dandi_zarr_checksum: digest}
    with pytest.raises(pydantic.ValidationError) as exc:
        models.BareAsset(
            contentSize=100,
            encodingFormat="application/x-zarr",
            digest=digest_model,
            path="/",
        )
    assert any(
        [
            "Digest must have an appropriate dandi-zarr-checksum value." in val
            for val in set([el["msg"] for el in exc.value.errors()])
        ]
    )
    digest = f"{32 * 'a'}-1--42"
    digest_model = {models.DigestType.dandi_zarr_checksum: digest}
    with pytest.raises(pydantic.ValidationError) as exc:
        models.BareAsset(
            contentSize=100,
            encodingFormat="application/x-zarr",
            digest=digest_model,
            path="/",
        )
    assert any(
        [
            "contentSize 100 is not equal to the checksum size 42." in val
            for val in set([el["msg"] for el in exc.value.errors()])
        ]
    )
    digest = f"{32 * 'a'}-1--100"
    digest_model = {models.DigestType.dandi_zarr_checksum: digest}
    with pytest.raises(pydantic.ValidationError) as exc:
        models.PublishedAsset(  # type: ignore[call-arg]
            contentSize=100,
            encodingFormat="application/x-zarr",
            digest=digest_model,
            path="/",
        )
    assert all(err["type"] == "missing" for err in exc.value.errors())
    digest_model = {
        models.DigestType.dandi_zarr_checksum: digest,
        models.DigestType.dandi_etag: digest + "-1",
    }
    with pytest.raises(pydantic.ValidationError) as exc:
        models.BareAsset(
            contentSize=100,
            encodingFormat="application/x-zarr",
            digest=digest_model,
            path="/",
        )
    assert any(
        [
            "Digest cannot have both etag and zarr checksums." in val
            for val in set([el["msg"] for el in exc.value.errors()])
        ]
    )
    with pytest.raises(pydantic.ValidationError) as exc:
        models.PublishedAsset(  # type: ignore[call-arg]
            contentSize=100,
            encodingFormat="application/x-zarr",
            digest=digest_model,
            path="/",
        )
    assert any(
        [
            "Digest cannot have both etag and zarr checksums." in val
            for val in set([el["msg"] for el in exc.value.errors()])
        ]
    )
    digest_model = {}
    with pytest.raises(pydantic.ValidationError) as exc:
        models.BareAsset(
            contentSize=100,
            encodingFormat="application/x-zarr",
            digest=digest_model,
            path="/",
        )
    assert any(
        [
            "A zarr asset must have a zarr checksum." in val
            for val in set([el["msg"] for el in exc.value.errors()])
        ]
    )
    with pytest.raises(pydantic.ValidationError) as exc:
        models.PublishedAsset(  # type: ignore[call-arg]
            contentSize=100,
            encodingFormat="application/x-zarr",
            digest=digest_model,
            path="/",
        )
    assert any(
        [
            "A zarr asset must have a zarr checksum." in val
            for val in set([el["msg"] for el in exc.value.errors()])
        ]
    )


@pytest.mark.parametrize(
    "enumtype,values",
    [
        (
            AccessType,
            {
                "OpenAccess": "dandi:OpenAccess",
                "EmbargoedAccess": "dandi:EmbargoedAccess",
                # "RestrictedAccess": "dandi:RestrictedAccess",
            },
        ),
        (
            RoleType,
            {
                "Author": "dcite:Author",
                "Conceptualization": "dcite:Conceptualization",
                "ContactPerson": "dcite:ContactPerson",
                "DataCollector": "dcite:DataCollector",
                "DataCurator": "dcite:DataCurator",
                "DataManager": "dcite:DataManager",
                "FormalAnalysis": "dcite:FormalAnalysis",
                "FundingAcquisition": "dcite:FundingAcquisition",
                "Investigation": "dcite:Investigation",
                "Maintainer": "dcite:Maintainer",
                "Methodology": "dcite:Methodology",
                "Producer": "dcite:Producer",
                "ProjectLeader": "dcite:ProjectLeader",
                "ProjectManager": "dcite:ProjectManager",
                "ProjectMember": "dcite:ProjectMember",
                "ProjectAdministration": "dcite:ProjectAdministration",
                "Researcher": "dcite:Researcher",
                "Resources": "dcite:Resources",
                "Software": "dcite:Software",
                "Supervision": "dcite:Supervision",
                "Validation": "dcite:Validation",
                "Visualization": "dcite:Visualization",
                "Funder": "dcite:Funder",
                "Sponsor": "dcite:Sponsor",
                "StudyParticipant": "dcite:StudyParticipant",
                "Affiliation": "dcite:Affiliation",
                "EthicsApproval": "dcite:EthicsApproval",
                "Other": "dcite:Other",
            },
        ),
        (
            RelationType,
            {
                "IsCitedBy": "dcite:IsCitedBy",
                "Cites": "dcite:Cites",
                "IsSupplementTo": "dcite:IsSupplementTo",
                "IsSupplementedBy": "dcite:IsSupplementedBy",
                "IsContinuedBy": "dcite:IsContinuedBy",
                "Continues": "dcite:Continues",
                "Describes": "dcite:Describes",
                "IsDescribedBy": "dcite:IsDescribedBy",
                "HasMetadata": "dcite:HasMetadata",
                "IsMetadataFor": "dcite:IsMetadataFor",
                "HasVersion": "dcite:HasVersion",
                "IsVersionOf": "dcite:IsVersionOf",
                "IsNewVersionOf": "dcite:IsNewVersionOf",
                "IsPreviousVersionOf": "dcite:IsPreviousVersionOf",
                "IsPartOf": "dcite:IsPartOf",
                "HasPart": "dcite:HasPart",
                "IsReferencedBy": "dcite:IsReferencedBy",
                "References": "dcite:References",
                "IsDocumentedBy": "dcite:IsDocumentedBy",
                "Documents": "dcite:Documents",
                "IsCompiledBy": "dcite:IsCompiledBy",
                "Compiles": "dcite:Compiles",
                "IsVariantFormOf": "dcite:IsVariantFormOf",
                "IsOriginalFormOf": "dcite:IsOriginalFormOf",
                "IsIdenticalTo": "dcite:IsIdenticalTo",
                "IsReviewedBy": "dcite:IsReviewedBy",
                "Reviews": "dcite:Reviews",
                "IsDerivedFrom": "dcite:IsDerivedFrom",
                "IsSourceOf": "dcite:IsSourceOf",
                "IsRequiredBy": "dcite:IsRequiredBy",
                "Requires": "dcite:Requires",
                "Obsoletes": "dcite:Obsoletes",
                "IsObsoletedBy": "dcite:IsObsoletedBy",
                "IsPublishedIn": "dcite:IsPublishedIn",
            },
        ),
        (
            ParticipantRelationType,
            {
                "isChildOf": "dandi:isChildOf",
                "isDizygoticTwinOf": "dandi:isDizygoticTwinOf",
                "isMonozygoticTwinOf": "dandi:isMonozygoticTwinOf",
                "isSiblingOf": "dandi:isSiblingOf",
                "isParentOf": "dandi:isParentOf",
            },
        ),
        (
            LicenseType,
            {
                "CC0_10": "spdx:CC0-1.0",
                "CC_BY_40": "spdx:CC-BY-4.0",
            },
        ),
        (
            IdentifierType,
            {
                "doi": "dandi:doi",
                "orcid": "dandi:orcid",
                "ror": "dandi:ror",
                "dandi": "dandi:dandi",
                "rrid": "dandi:rrid",
            },
        ),
        (
            DigestType,
            {
                "md5": "dandi:md5",
                "sha1": "dandi:sha1",
                "sha2_256": "dandi:sha2-256",
                "sha3_256": "dandi:sha3-256",
                "blake2b_256": "dandi:blake2b-256",
                "blake3": "dandi:blake3",
                "dandi_etag": "dandi:dandi-etag",
                "dandi_zarr_checksum": "dandi:dandi-zarr-checksum",
            },
        ),
        (
            AgeReferenceType,
            {
                "BirthReference": "dandi:BirthReference",
                "GestationalReference": "dandi:GestationalReference",
            },
        ),
    ],
)
def test_types(enumtype: Type[Enum], values: Dict[str, str]) -> None:
    assert {v.name: v.value for v in enumtype} == values


def test_autogenerated_titles() -> None:
    schema = Asset.model_json_schema(schema_generator=TransitionalGenerateJsonSchema)
    assert schema["title"] == "Asset"
    assert schema["properties"]["schemaVersion"]["title"] == "Schema Version"
    assert schema["$defs"]["PropertyValue"]["title"] == "Property Value"


def test_dantimeta_1() -> None:
    """checking basic metadata for publishing"""
    # meta data without doi, datePublished and publishedBy
    meta_dict: Dict[str, Any] = {
        "identifier": "DANDI:999999",
        "id": "DANDI:999999/draft",
        "version": "1.0.0",
        "name": "testing dataset",
        "description": "testing",
        "contributor": [
            {
                "name": "last name, first name",
                "email": "someone@dandiarchive.org",
                "roleName": [RoleType("dcite:ContactPerson")],
                "schemaKey": "Person",
            }
        ],
        "license": [LicenseType("spdx:CC-BY-4.0")],
        "citation": "Last, first (2021). Test citation.",
        "assetsSummary": {
            "numberOfBytes": 0,
            "numberOfFiles": 0,
            "dataStandard": [{"name": "NWB"}],
            "approach": [{"name": "electrophysiology"}],
            "measurementTechnique": [{"name": "two-photon microscopy technique"}],
            "species": [{"name": "Human"}],
        },
        "manifestLocation": [
            "https://api.dandiarchive.org/api/dandisets/999999/versions/draft/assets/"
        ],
        "url": "https://dandiarchive.org/dandiset/999999/draft",
    }

    # should work for Dandiset but PublishedDandiset should raise an error
    Dandiset(**meta_dict)
    with pytest.raises(ValidationError) as exc:
        PublishedDandiset(**meta_dict)

    ErrDetail = namedtuple("ErrDetail", ["type", "msg"])

    # Expected errors keyed by location of the respective error
    # Note: Pydantic generated error messages are not provided for they are not in our
    #       control, and the error type should be indicative enough.
    expected_errors: Dict[Tuple[Union[int, str], ...], ErrDetail] = {
        ("id",): ErrDetail(type="string_pattern_mismatch", msg=None),
        ("publishedBy",): ErrDetail(type="missing", msg=None),
        ("datePublished",): ErrDetail(type="missing", msg=None),
        ("url",): ErrDetail(
            type="value_error",
            msg="Value error, string does not match regex "
            f'"^{DANDI_INSTANCE_URL_PATTERN}/dandiset/'
            '\\d{6}/\\d+\\.\\d+\\.\\d+$"',
        ),
        ("assetsSummary",): ErrDetail(
            type="value_error",
            msg="Value error, "
            "A Dandiset containing no files or zero bytes is not publishable",
        ),
        ("doi",): ErrDetail(type="missing", msg=None),
    }

    assert len(exc.value.errors()) == 6
    for err in exc.value.errors():
        err_loc = err["loc"]
        assert err_loc in expected_errors

        assert err["type"] == expected_errors[err_loc].type
        if expected_errors[err_loc].msg is not None:
            assert err["msg"] == expected_errors[err_loc].msg

    assert set([el["loc"][0] for el in exc.value.errors()]) == {
        "assetsSummary",
        "datePublished",
        "publishedBy",
        "doi",
        "url",
        "id",
    }

    # after adding basic meta required to publish: doi, datePublished, publishedBy, assetsSummary,
    # so PublishedDandiset should work
    meta_dict["url"] = "https://dandiarchive.org/dandiset/999999/0.0.0"
    meta_dict["id"] = "DANDI:999999/0.0.0"
    meta_dict["version"] = "0.0.0"
    meta_dict.update(_basic_publishmeta(dandi_id="999999"))
    meta_dict["assetsSummary"].update(**{"numberOfBytes": 1, "numberOfFiles": 1})
    meta_dict["releaseNotes"] = "Releasing during testing"
    PublishedDandiset(**meta_dict)


def test_schemakey() -> None:
    typemap = {
        "BareAsset": "Asset",
        "PublishedAsset": "Asset",
        "PublishedDandiset": "Dandiset",
    }
    for val in dir(models):
        if val in ["BaseModel"]:
            continue
        klass = getattr(models, val)
        if isclass(klass) and issubclass(klass, pydantic.BaseModel):
            assert "schemaKey" in klass.model_fields
            if val in typemap:
                assert typemap[val] == klass.model_fields["schemaKey"].default
            else:
                assert val == klass.model_fields["schemaKey"].default


def test_duplicate_classes() -> None:
    qnames: Dict[str, Optional[type]] = {}

    def check_qname(qname: str, klass: type) -> None:
        if (
            qname
            in [
                "dandi:id",
                "dandi:schemaKey",
            ]
            or qname.startswith("schema")
            or qname.startswith("prov")
        ):
            return
        if qname in qnames:
            t = qnames[qname]
            if t is None:
                return
            elif issubclass(klass, (t,)):
                return
            elif issubclass(t, klass):
                qnames[qname] = klass
                return
            if qname == "dandi:repository" and klass.__name__ in (
                "Resource",
                "CommonModel",
            ):
                return
            if qname == "dandi:relation" and klass.__name__ in (
                "Resource",
                "RelatedParticipant",
            ):
                return
            if qname in "dandi:approach" and klass.__name__ in (
                "Asset",
                "AssetsSummary",
            ):
                return
            if qname == "dandi:species" and klass.__name__ in (
                "Participant",
                "AssetsSummary",
            ):
                return
            raise ValueError(f"{qname},{klass} already exists {qnames[qname]}")
        qnames[qname] = klass

    modelnames = dir(models)
    modelnames.remove("CommonModel")
    modelnames.remove("BaseType")
    modelnames.remove("BaseModel")
    modelnames.remove("DandiBaseModel")
    for val in ["CommonModel", "BaseType"] + modelnames:
        klass = getattr(models, val)
        if not isclass(klass) or not issubclass(klass, pydantic.BaseModel):
            continue
        if hasattr(klass, "_ldmeta"):
            if "nskey" in klass._ldmeta.default:
                name = klass.__name__
                qname = f'{klass._ldmeta.default["nskey"]}:{name}'
            else:
                qname = f"dandi:{name}"
            check_qname(qname, klass)
        for name, field in klass.model_fields.items():
            if (
                isinstance(field.json_schema_extra, dict)
                and "nskey" in field.json_schema_extra
            ):
                qname = cast(str, field.json_schema_extra["nskey"]) + ":" + name
            else:
                qname = f"dandi:{name}"
            check_qname(qname, klass)


def test_properties_mismatch() -> None:
    prop_names = {}
    errors = []
    modelnames = dir(models)
    modelnames.remove("BaseModel")
    modelnames.remove("DandiBaseModel")
    modelnames.remove("CommonModel")
    modelnames.remove("Contributor")
    modelnames.remove("Publishable")
    for val in modelnames:
        klass = getattr(models, val)
        if not isclass(klass) or not issubclass(klass, pydantic.BaseModel):
            continue
        if not hasattr(klass, "_ldmeta") or "nskey" not in klass._ldmeta.default:
            errors.append(f"{klass} does not have nskey")
        for name, field in klass.model_fields.items():
            if field.json_schema_extra is None:
                nskey = "dandi"
            else:
                assert isinstance(field.json_schema_extra, dict)
                nskey = cast(str, field.json_schema_extra.get("nskey", "dandi"))
            if name not in prop_names:
                prop_names[name] = nskey
            elif nskey != prop_names[name]:
                errors.append(
                    f"{klass}:{name} has multiple nskeys: {nskey}, {prop_names[name]}"
                )
    assert errors == []


class TempKlass1(DandiBaseModel):
    contributor: Optional[List[Union[Organization, Person]]] = None
    schemaKey: Literal["TempKlass1"] = Field(
        "TempKlass1", validate_default=True, json_schema_extra={"readOnly": True}
    )


def test_schemakey_roundtrip() -> None:
    contributor = [
        {
            "name": "first",
            "roleName": [],
            "schemaKey": "Person",
            "affiliation": [],
            "includeInCitation": True,
        },
        {
            "name": "last2, first2",
            "email": "nospam@dandiarchive.org",
            "roleName": ["dcite:ContactPerson"],
            "schemaKey": "Person",
            "affiliation": [],
            "includeInCitation": True,
        },
    ]
    with pytest.raises(pydantic.ValidationError):
        TempKlass1(contributor=contributor)
    contributor[0]["name"] = ", "
    with pytest.raises(pydantic.ValidationError):
        TempKlass1(contributor=contributor)
    contributor[0]["name"] = "last, first"
    klassobj = TempKlass1(contributor=contributor)
    assert klassobj.contributor is not None and all(
        [isinstance(val, Person) for val in klassobj.contributor]
    )


class TempKlass2(DandiBaseModel):
    contributor: Person
    schemaKey: Literal["TempKlass2"] = Field(
        "TempKlass2", validate_default=True, json_schema_extra={"readOnly": True}
    )


@pytest.mark.parametrize("name", ["Mitášová, Helena", "O'Brien, Claire"])
def test_name_regex(name: str) -> None:
    contributor = {
        "name": name,
        "roleName": [],
        "schemaKey": "Person",
        "affiliation": [],
        "includeInCitation": True,
    }
    TempKlass2(contributor=contributor)


def test_resource() -> None:
    with pytest.raises(pydantic.ValidationError):
        Resource(relation=RelationType.IsCitedBy)
    Resource(identifier="123", relation=RelationType.IsCitedBy)
    Resource(url="http://example.org/resource", relation=RelationType.IsCitedBy)


def test_basetype() -> None:
    props = BaseType.model_json_schema(schema_generator=TransitionalGenerateJsonSchema)[
        "properties"
    ]
    identifier = props["identifier"]
    assert "anyOf" not in identifier
    assert identifier.get("maxLength") == 1000
    key = props["schemaKey"]
    assert key["const"] == "BaseType"


def test_https_regex() -> None:
    props = Affiliation.model_json_schema(
        schema_generator=TransitionalGenerateJsonSchema
    )["properties"]["identifier"]
    assert props["format"] == "uri"
    assert props.get("maxLength") == 1000


def test_schemakey_in_required() -> None:
    props = Affiliation.model_json_schema(
        schema_generator=TransitionalGenerateJsonSchema
    )["required"]
    assert "schemaKey" in props


@pytest.mark.parametrize("value", [None, [], {}, (), ""])
def test_propertyvalue(value: Any) -> None:
    with pytest.raises(pydantic.ValidationError):
        PropertyValue(value=value)


def test_propertyvalue_valid() -> None:
    PropertyValue(value=1)


def test_propertyvalue_json() -> None:
    reqprops = PropertyValue.model_json_schema(
        schema_generator=TransitionalGenerateJsonSchema
    )["$defs"]["PropertyValue"]["required"]
    assert "value" == reqprops[1]


def test_embargoedaccess() -> None:
    with pytest.raises(pydantic.ValidationError):
        CommonModel(access=[AccessRequirements(status=AccessType.EmbargoedAccess)])
    CommonModel(
        access=[
            AccessRequirements(
                status=AccessType.EmbargoedAccess, embargoedUntil="2022-12-31"
            )
        ]
    )


_NON_CONTACT_PERSON_ROLES_ARGS: List[List[RoleType]] = [
    [],
    [RoleType.Author, RoleType.DataCurator],
    [RoleType.Funder],
]

_CONTACT_PERSON_ROLES_ARGS: List[List[RoleType]] = [
    role_lst + [RoleType.ContactPerson] for role_lst in _NON_CONTACT_PERSON_ROLES_ARGS
]


class TestContributor:

    @pytest.mark.parametrize("roles", _CONTACT_PERSON_ROLES_ARGS)
    def test_contact_person_without_email(self, roles: List[RoleType]) -> None:
        """
        Test creating a `Contributor` instance as a contact person without an email
        """
        with pytest.raises(
            pydantic.ValidationError, match="Contact person must have an email address"
        ):
            Contributor(roleName=roles)

    @pytest.mark.parametrize("roles", _NON_CONTACT_PERSON_ROLES_ARGS)
    def test_non_contact_person_without_email(self, roles: List[RoleType]) -> None:
        """
        Test creating a `Contributor` instance as a non-contact person without an email
        """
        Contributor(roleName=roles)

    @pytest.mark.parametrize(
        "roles", _NON_CONTACT_PERSON_ROLES_ARGS + _CONTACT_PERSON_ROLES_ARGS
    )
    def test_with_email(self, roles: List[RoleType]) -> None:
        """
        Test creating a `Contributor` instance with an email
        """
        Contributor(email="nemo@dandiarchive.org", roleName=roles)
