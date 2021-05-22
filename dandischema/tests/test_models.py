import pydantic
from pydantic import ValidationError
import pytest

from .test_datacite import _basic_publishmeta
from .. import models
from ..models import (
    AccessType,
    AssetMeta,
    DandisetMeta,
    DigestType,
    IdentifierType,
    LicenseType,
    ParticipantRelationType,
    PublishedDandisetMeta,
    RelationType,
    RoleType,
)


def test_dandiset():
    assert DandisetMeta.unvalidated()


def test_asset():
    assert AssetMeta.unvalidated()


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
                "Author": "dandirole:Author",
                "Conceptualization": "dandirole:Conceptualization",
                "ContactPerson": "dandirole:ContactPerson",
                "DataCollector": "dandirole:DataCollector",
                "DataCurator": "dandirole:DataCurator",
                "DataManager": "dandirole:DataManager",
                "FormalAnalysis": "dandirole:FormalAnalysis",
                "FundingAcquisition": "dandirole:FundingAcquisition",
                "Investigation": "dandirole:Investigation",
                "Maintainer": "dandirole:Maintainer",
                "Methodology": "dandirole:Methodology",
                "Producer": "dandirole:Producer",
                "ProjectLeader": "dandirole:ProjectLeader",
                "ProjectManager": "dandirole:ProjectManager",
                "ProjectMember": "dandirole:ProjectMember",
                "ProjectAdministration": "dandirole:ProjectAdministration",
                "Researcher": "dandirole:Researcher",
                "Resources": "dandirole:Resources",
                "Software": "dandirole:Software",
                "Supervision": "dandirole:Supervision",
                "Validation": "dandirole:Validation",
                "Visualization": "dandirole:Visualization",
                "Funder": "dandirole:Funder",
                "Sponsor": "dandirole:Sponsor",
                "StudyParticipant": "dandirole:StudyParticipant",
                "Affiliation": "dandirole:Affiliation",
                "EthicsApproval": "dandirole:EthicsApproval",
                "Other": "dandirole:Other",
            },
        ),
        (
            RelationType,
            {
                "IsCitedBy": "dandi:IsCitedBy",
                "Cites": "dandi:Cites",
                "IsSupplementTo": "dandi:IsSupplementTo",
                "IsSupplementedBy": "dandi:IsSupplementedBy",
                "IsContinuedBy": "dandi:IsContinuedBy",
                "Continues": "dandi:Continues",
                "Describes": "dandi:Describes",
                "IsDescribedBy": "dandi:IsDescribedBy",
                "HasMetadata": "dandi:HasMetadata",
                "IsMetadataFor": "dandi:IsMetadataFor",
                "HasVersion": "dandi:HasVersion",
                "IsVersionOf": "dandi:IsVersionOf",
                "IsNewVersionOf": "dandi:IsNewVersionOf",
                "IsPreviousVersionOf": "dandi:IsPreviousVersionOf",
                "IsPartOf": "dandi:IsPartOf",
                "HasPart": "dandi:HasPart",
                "IsReferencedBy": "dandi:IsReferencedBy",
                "References": "dandi:References",
                "IsDocumentedBy": "dandi:IsDocumentedBy",
                "Documents": "dandi:Documents",
                "IsCompiledBy": "dandi:IsCompiledBy",
                "Compiles": "dandi:Compiles",
                "IsVariantFormOf": "dandi:IsVariantFormOf",
                "IsOriginalFormOf": "dandi:IsOriginalFormOf",
                "IsIdenticalTo": "dandi:IsIdenticalTo",
                "IsReviewedBy": "dandi:IsReviewedBy",
                "Reviews": "dandi:Reviews",
                "IsDerivedFrom": "dandi:IsDerivedFrom",
                "IsSourceOf": "dandi:IsSourceOf",
                "IsRequiredBy": "dandi:IsRequiredBy",
                "Requires": "dandi:Requires",
                "Obsoletes": "dandi:Obsoletes",
                "IsObsoletedBy": "dandi:IsObsoletedBy",
            },
        ),
        (
            ParticipantRelationType,
            {
                "IsChildOf": "dandi:IsChildOf",
                "IsDizygoticTwinOf": "dandi:IsDizygoticTwinOf",
                "IsMonozygoticTwinOf": "dandi:IsMonozygoticTwinOf",
                "IsSiblingOf": "dandi:IsSiblingOf",
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
    schema = AssetMeta.schema()
    assert schema["title"] == "Asset Meta"
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
                "roleName": [RoleType("dandirole:ContactPerson")],
            }
        ],
        "license": [LicenseType("spdx:CC-BY-4.0")],
        "citation": "Last, first (2021). Test citation.",
        "assetsSummary": {
            "numberOfBytes": 10,
            "numberOfFiles": 1,
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

    # should work for DandisetMeta but PublishedDandisetMeta should raise an error
    DandisetMeta(**meta_dict)
    with pytest.raises(ValidationError) as exc:
        PublishedDandisetMeta(**meta_dict)

    assert all([el["msg"] == "field required" for el in exc.value.errors()])
    assert set([el["loc"][0] for el in exc.value.errors()]) == {
        "datePublished",
        "publishedBy",
        "doi",
    }

    # after adding basic meta required to publish: doi, datePublished, publishedBy, assetsSummary,
    # so PublishedDandisetMeta should work
    meta_dict.update(_basic_publishmeta(dandi_id="DANDI:999999"))
    PublishedDandisetMeta(**meta_dict)


def test_schemakey():
    typemap = {
        "AssetMeta": "Asset",
        "BareAssetMeta": "Asset",
        "DandisetMeta": "Dandiset",
        "PublishedAssetMeta": "Asset",
        "PublishedDandisetMeta": "Dandiset",
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
