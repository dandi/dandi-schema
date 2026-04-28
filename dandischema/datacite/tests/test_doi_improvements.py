"""
Tests for DataCite DOI improvements.

T001: Optional doi field on Dandiset model for concept DOIs
T002: dates field in to_datacite() output
T003: IsVersionOf/HasVersion relation support in to_datacite()

Note: These tests were AI-generated (Claude Code) using TDD methodology.
"""

import random
from typing import Any, Dict

import pytest

from dandischema.conf import get_instance_config
from dandischema.models import (
    Dandiset,
    LicenseType,
    RoleType,
)
from dandischema.tests.utils import (
    DOI_PREFIX,
    INSTANCE_NAME,
    basic_publishmeta,
    skipif_no_doi_prefix,
)

from .. import to_datacite

_INSTANCE_CONFIG = get_instance_config()


@pytest.fixture(scope="function")
def metadata_with_publish() -> Dict[str, Any]:
    """Create a complete metadata dict suitable for PublishedDandiset."""
    dandi_id_noprefix = f"000{random.randrange(100, 999)}"
    dandi_id = f"{INSTANCE_NAME}:{dandi_id_noprefix}"
    version = "0.0.0"
    meta_dict = {
        "identifier": dandi_id,
        "id": f"{dandi_id}/{version}",
        "name": "Test DOI Improvements Dataset",
        "description": "Testing DOI metadata improvements",
        "contributor": [
            {
                "name": "Test_last, Test_first",
                "email": "test@example.com",
                "roleName": [RoleType("dcite:ContactPerson")],
                "schemaKey": "Person",
            }
        ],
        "license": [LicenseType("spdx:CC-BY-4.0")],
        "url": f"https://dandiarchive.org/dandiset/{dandi_id_noprefix}/{version}",
        "version": version,
        "citation": "Test_last, Test_first 2026",
        "manifestLocation": [
            f"https://api.dandiarchive.org/api/dandisets/{dandi_id_noprefix}/versions/draft/assets/"
        ],
        "assetsSummary": {
            "schemaKey": "AssetsSummary",
            "numberOfBytes": 100,
            "numberOfFiles": 2,
            "dataStandard": [{"schemaKey": "StandardsType", "name": "NWB"}],
            "approach": [{"schemaKey": "ApproachType", "name": "electrophysiology"}],
            "measurementTechnique": [
                {
                    "schemaKey": "MeasurementTechniqueType",
                    "name": "two-photon microscopy technique",
                }
            ],
            "species": [{"schemaKey": "SpeciesType", "name": "Human"}],
        },
    }
    if DOI_PREFIX is not None:
        meta_dict.update(
            basic_publishmeta(
                INSTANCE_NAME, dandi_id=dandi_id_noprefix, prefix=DOI_PREFIX
            )
        )
    return meta_dict


# =============================================================================
# T001: Optional doi field on Dandiset model for concept DOIs
# =============================================================================


class TestDandisetConceptDoi:
    """T001: The Dandiset model should accept an optional doi field."""

    @skipif_no_doi_prefix
    def test_dandiset_accepts_doi_field(
        self, metadata_with_publish: Dict[str, Any]
    ) -> None:
        """Dandiset model should accept a doi field without error."""
        meta = metadata_with_publish.copy()
        dandi_id_noprefix = meta["identifier"].split(":")[1]
        # Construct a concept DOI (no version suffix)
        concept_doi = f"{DOI_PREFIX}/{INSTANCE_NAME.lower()}.{dandi_id_noprefix}"

        # Build a Dandiset (not PublishedDandiset) with a doi
        dandiset_meta = {
            k: v
            for k, v in meta.items()
            if k not in ("datePublished", "publishedBy", "doi")
        }
        dandiset_meta["doi"] = concept_doi

        # This should not raise — Dandiset should accept an optional doi
        dandiset = Dandiset(**dandiset_meta)
        assert dandiset.doi == concept_doi

    def test_dandiset_doi_is_optional(
        self, metadata_with_publish: Dict[str, Any]
    ) -> None:
        """Dandiset model should work without a doi field (default None)."""
        meta = metadata_with_publish.copy()
        dandiset_meta = {
            k: v
            for k, v in meta.items()
            if k not in ("datePublished", "publishedBy", "doi")
        }
        # No doi field — should still work
        dandiset = Dandiset(**dandiset_meta)
        assert dandiset.doi is None


# =============================================================================
# T002: dates field in to_datacite() output
# =============================================================================


class TestDataciteDatesField:
    """T002: to_datacite() should include a dates field with dateType Issued."""

    @skipif_no_doi_prefix
    def test_dates_field_present(self, metadata_with_publish: Dict[str, Any]) -> None:
        """DataCite output should contain a 'dates' attribute."""
        datacite = to_datacite(metadata_with_publish)
        attrs = datacite["data"]["attributes"]
        assert "dates" in attrs, "dates field missing from DataCite output"

    @skipif_no_doi_prefix
    def test_dates_field_has_issued_type(
        self, metadata_with_publish: Dict[str, Any]
    ) -> None:
        """The dates field should contain an entry with dateType 'Issued'."""
        datacite = to_datacite(metadata_with_publish)
        attrs = datacite["data"]["attributes"]
        dates = attrs.get("dates", [])
        issued_dates = [d for d in dates if d.get("dateType") == "Issued"]
        assert len(issued_dates) == 1, "Expected exactly one Issued date entry"

    @skipif_no_doi_prefix
    def test_dates_field_value_matches_publication_year(
        self, metadata_with_publish: Dict[str, Any]
    ) -> None:
        """The Issued date value should correspond to datePublished."""
        datacite = to_datacite(metadata_with_publish)
        attrs = datacite["data"]["attributes"]
        dates = attrs.get("dates", [])
        issued_dates = [d for d in dates if d.get("dateType") == "Issued"]
        assert len(issued_dates) == 1
        # The date string should contain the publication year
        pub_year = attrs["publicationYear"]
        assert pub_year in issued_dates[0]["date"]


# =============================================================================
# T003: IsVersionOf/HasVersion relation support in to_datacite()
# =============================================================================


class TestDataciteConceptDoiRelations:
    """T003: to_datacite() should support concept DOI relations."""

    @skipif_no_doi_prefix
    def test_is_version_of_relation_added(
        self, metadata_with_publish: Dict[str, Any]
    ) -> None:
        """When concept_doi is provided, an IsVersionOf relatedIdentifier should appear."""
        dandi_id_noprefix = metadata_with_publish["identifier"].split(":")[1]
        concept_doi = f"{DOI_PREFIX}/{INSTANCE_NAME.lower()}.{dandi_id_noprefix}"

        datacite = to_datacite(metadata_with_publish, concept_doi=concept_doi)
        attrs = datacite["data"]["attributes"]

        related = attrs.get("relatedIdentifiers", [])
        is_version_of = [r for r in related if r.get("relationType") == "IsVersionOf"]
        assert len(is_version_of) == 1, "Expected one IsVersionOf relation"
        assert is_version_of[0]["relatedIdentifier"] == concept_doi
        assert is_version_of[0]["relatedIdentifierType"] == "DOI"

    @skipif_no_doi_prefix
    def test_no_concept_doi_no_relation(
        self, metadata_with_publish: Dict[str, Any]
    ) -> None:
        """When concept_doi is not provided, no IsVersionOf relation should appear."""
        datacite = to_datacite(metadata_with_publish)
        attrs = datacite["data"]["attributes"]

        related = attrs.get("relatedIdentifiers", [])
        is_version_of = [r for r in related if r.get("relationType") == "IsVersionOf"]
        assert (
            len(is_version_of) == 0
        ), "No IsVersionOf relation expected without concept_doi"


# =============================================================================
# T004: DANDI identifier in alternateIdentifiers + version in Version property
# =============================================================================


class TestDataciteVersionProperty:
    """DataCite output should include version property."""

    @skipif_no_doi_prefix
    def test_version_property_populated(
        self, metadata_with_publish: Dict[str, Any]
    ) -> None:
        """The 'version' attribute should be populated in the DataCite output."""
        datacite = to_datacite(metadata_with_publish)
        attrs = datacite["data"]["attributes"]
        # version should already be present, but verify it matches the input
        assert "version" in attrs
        assert attrs["version"] == metadata_with_publish["version"]
