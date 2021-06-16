import enum

import pydantic
from pydantic import ValidationError
import pytest

from .test_datacite import _basic_publishmeta
from .. import models
from ..models import (
    AccessType,
    Asset,
    Dandiset,
    DigestType,
    IdentifierType,
    LicenseType,
    ParticipantRelationType,
    PublishedDandiset,
    RelationType,
    RoleType,
)


def test_dandiset():
    assert Dandiset.unvalidated()


def test_asset():
    assert Asset.unvalidated()


def test_asset_digest():
    digest_model = {"sha1": ""}
    with pytest.raises(pydantic.ValidationError) as exc:
        models.BareAsset(
            contentSize=100, encodingFormat="nwb", digest=digest_model, path="/"
        )
    assert any(
        [
            "value is not a valid enumeration member" in val
            for val in set([el["msg"] for el in exc.value.errors()])
        ]
    )
    digest_type = "dandi_etag"
    digest = 32 * "a"
    digest_model = {models.DigestType[digest_type]: digest}
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
    digest_model = {models.DigestType[digest_type]: digest}
    models.BareAsset(
        contentSize=100, encodingFormat="nwb", digest=digest_model, path="/"
    )
    digest_model = {models.DigestType[digest_type]: digest, "sha1": ""}
    with pytest.raises(pydantic.ValidationError) as exc:
        models.PublishedAsset(
            contentSize=100, encodingFormat="nwb", digest=digest_model, path="/"
        )
    assert any(
        [
            "value is not a valid enumeration member" in val
            for val in set([el["msg"] for el in exc.value.errors()])
        ]
    )
    digest_model = {
        models.DigestType[digest_type]: digest,
        models.DigestType.sha2_256: 63 * "a",
    }
    with pytest.raises(pydantic.ValidationError) as exc:
        models.PublishedAsset(
            contentSize=100, encodingFormat="nwb", digest=digest_model, path="/"
        )
    assert "Digest is missing sha2_256 value" in set(
        [el["msg"] for el in exc.value.errors()]
    )
    digest_model = {
        models.DigestType[digest_type]: digest,
        models.DigestType.sha2_256: 64 * "a",
    }
    with pytest.raises(pydantic.ValidationError) as exc:
        models.PublishedAsset(
            contentSize=100, encodingFormat="nwb", digest=digest_model, path="/"
        )
    assert "Digest is missing sha2_256 value" not in set(
        [el["msg"] for el in exc.value.errors()]
    )


@pytest.mark.parametrize(
    "enumtype,values",
    [
        (
            AccessType,
            {
                "OpenAccess": "dandi:OpenAccess",
                # "EmbargoedAccess": "dandi:EmbargoedAccess",
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
                "CC_BY_NC_40": "spdx:CC-BY-NC-4.0",
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
            },
        ),
    ],
)
def test_types(enumtype, values):
    assert {v.name: v.value for v in enumtype} == values


def test_autogenerated_titles():
    schema = Asset.schema()
    assert schema["title"] == "Asset"
    assert schema["properties"]["schemaVersion"]["title"] == "Schema Version"
    assert schema["definitions"]["PropertyValue"]["title"] == "Property Value"


def test_dantimeta_1():
    """ checking basic metadata for publishing"""
    # meta data without doi, datePublished and publishedBy
    meta_dict = {
        "identifier": "DANDI:999999",
        "id": "DANDI:999999/draft",
        "version": "v.1",
        "name": "testing dataset",
        "description": "testing",
        "contributor": [
            {
                "name": "last name, first name",
                "roleName": [RoleType("dcite:ContactPerson")],
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

    error_msgs = [
        "field required",
        "A Dandiset containing no files or zero bytes is not publishable",
    ]
    assert all([el["msg"] in error_msgs for el in exc.value.errors()])
    assert set([el["loc"][0] for el in exc.value.errors()]) == {
        "assetsSummary",
        "datePublished",
        "publishedBy",
        "doi",
    }

    # after adding basic meta required to publish: doi, datePublished, publishedBy, assetsSummary,
    # so PublishedDandiset should work
    meta_dict.update(_basic_publishmeta(dandi_id="DANDI:999999"))
    meta_dict["assetsSummary"].update(**{"numberOfBytes": 1, "numberOfFiles": 1})
    PublishedDandiset(**meta_dict)


def test_schemakey():
    typemap = {
        "BareAsset": "Asset",
        "PublishedAsset": "Asset",
        "PublishedDandiset": "Dandiset",
    }
    for val in dir(models):
        if val in ["BaseModel"]:
            continue
        klass = getattr(models, val)
        if isinstance(klass, pydantic.main.ModelMetaclass):
            assert "schemaKey" in klass.__fields__
            if val in typemap:
                assert typemap[val] == klass.__fields__["schemaKey"].default
            else:
                assert val == klass.__fields__["schemaKey"].default


def test_duplicate_classes():
    qnames = {}

    def check_qname(qname, klass):
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
            if qnames[qname] is None:
                return
            if issubclass(klass, (qnames[qname],)):
                return
            if issubclass(qnames[qname], klass):
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
        if not isinstance(klass, pydantic.main.ModelMetaclass):
            continue
        if isinstance(klass, enum.EnumMeta):
            for enumval in klass:
                qname = enumval.value
                check_qname(qname, klass)
        if hasattr(klass, "_ldmeta"):
            if "nskey" in klass._ldmeta:
                name = klass.__name__
                qname = f'{klass._ldmeta["nskey"]}:{name}'
            else:
                qname = f"dandi:{name}"
            check_qname(qname, klass)
        for name, field in klass.__fields__.items():
            if "nskey" in field.field_info.extra:
                qname = field.field_info.extra["nskey"] + ":" + name
            else:
                qname = f"dandi:{name}"
            check_qname(qname, klass)
