import copy
from typing import Any, Dict

import pytest

from dandischema.utils import google_dataset_metadata


@pytest.fixture
def sample_dandiset_metadata() -> Dict[str, Any]:
    """Sample DANDI metadata for testing"""
    return {
        "@context": "https://raw.githubusercontent.com/dandi/schema/master/releases/0.6.4/context.json",
        "schemaKey": "Dandiset",
        "identifier": "DANDI:000707",
        "name": "Test Dandiset",
        "description": "A test dandiset for testing Google Dataset Search compatibility",
        "contributor": [
            {
                "schemaKey": "Person",
                "name": "Doe, John",
                "roleName": ["dcite:Author", "dcite:ContactPerson"],
                "identifier": "0000-0001-2345-6789",
                "email": "john.doe@example.com",
                "includeInCitation": True,
            },
            {
                "schemaKey": "Organization",
                "name": "Test Organization",
                "roleName": ["dcite:Sponsor"],
                "identifier": "https://ror.org/xxxxxxxxx",
                "includeInCitation": False,
            },
        ],
        "license": ["spdx:CC-BY-4.0"],
        "schemaVersion": "0.6.4",
        "assetsSummary": {
            "schemaKey": "AssetsSummary",
            "numberOfBytes": 1000000,
            "numberOfFiles": 10,
            "dataStandard": [
                {
                    "name": "Neurodata Without Borders (NWB)",
                    "identifier": "RRID:SCR_015242",
                }
            ],
            "species": [
                {
                    "name": "Homo sapiens",
                    "identifier": "http://purl.obolibrary.org/obo/NCBITaxon_9606",
                }
            ],
            "approach": [
                {
                    "name": "electrophysiology",
                    "identifier": "http://uri.interlex.org/base/ilx_0739363",
                }
            ],
            "measurementTechnique": [
                {
                    "name": "multi-electrode extracellular electrophysiology",
                    "identifier": "http://uri.interlex.org/base/ilx_0739400",
                }
            ],
        },
    }


def test_google_dataset_metadata_basic_transformation(sample_dandiset_metadata):
    """Test that the basic transformation works correctly"""
    result = google_dataset_metadata(sample_dandiset_metadata)

    # Check that the original metadata is not modified
    assert sample_dandiset_metadata != result

    # Check that schema:Dataset is added to schemaKey
    assert "schema:Dataset" in result["schemaKey"]

    # Check that creator is properly formatted
    assert "creator" in result
    assert isinstance(result["creator"], list)
    assert len(result["creator"]) > 0

    # Check first creator
    creator = result["creator"][0]
    assert creator["schemaKey"] == "schema:Person"
    assert "name" in creator

    # Check that license is properly formatted
    assert "license" in result
    assert isinstance(result["license"], list)
    assert "https://spdx.org/licenses/CC-BY-4.0" in result["license"]

    # Check that version is present
    assert "version" in result

    # Check that identifier is properly formatted
    assert "identifier" in result
    assert result["identifier"] == "https://identifiers.org/DANDI:000707"

    # Check that keywords exist
    assert "keywords" in result
    assert isinstance(result["keywords"], list)
    assert len(result["keywords"]) > 0
    assert "neuroscience" in result["keywords"]
    assert "DANDI" in result["keywords"]


def test_google_dataset_metadata_preserves_original(sample_dandiset_metadata):
    """Test that the original metadata is not modified"""
    original = copy.deepcopy(sample_dandiset_metadata)
    google_dataset_metadata(sample_dandiset_metadata)

    # Verify the original is unchanged
    assert original == sample_dandiset_metadata


def test_google_dataset_metadata_with_existing_creator(sample_dandiset_metadata):
    """Test that existing creator is preserved"""
    # Add a creator field
    sample_dandiset_metadata["creator"] = [
        {
            "schemaKey": "Person",
            "name": "Jane Smith",
            "identifier": "https://orcid.org/0000-0002-3456-7890",
        }
    ]

    result = google_dataset_metadata(sample_dandiset_metadata)

    # Check that the existing creator is preserved
    assert result["creator"] == sample_dandiset_metadata["creator"]


def test_google_dataset_metadata_with_existing_keywords(sample_dandiset_metadata):
    """Test that existing keywords are preserved and extended"""
    # Add keywords field
    sample_dandiset_metadata["keywords"] = ["test", "example"]

    result = google_dataset_metadata(sample_dandiset_metadata)

    # Check that the existing keywords are preserved
    assert "test" in result["keywords"]
    assert "example" in result["keywords"]

    # Check that additional keywords are added
    assert "neuroscience" in result["keywords"]
    assert "DANDI" in result["keywords"]


def test_google_dataset_metadata_with_no_license(sample_dandiset_metadata):
    """Test handling when no license is present"""
    # Remove license field
    no_license_metadata = copy.deepcopy(sample_dandiset_metadata)
    del no_license_metadata["license"]

    result = google_dataset_metadata(no_license_metadata)

    # Check that license is not in the result
    assert "license" not in result


def test_google_dataset_metadata_with_no_contributors(sample_dandiset_metadata):
    """Test handling when no contributors are present"""
    # Remove contributor field
    no_contributor_metadata = copy.deepcopy(sample_dandiset_metadata)
    del no_contributor_metadata["contributor"]

    result = google_dataset_metadata(no_contributor_metadata)

    # Check that creator is not in the result
    assert "creator" not in result


def test_google_dataset_metadata_with_date_published(sample_dandiset_metadata):
    """Test handling of datePublished field"""
    # Add datePublished field
    sample_dandiset_metadata["datePublished"] = "2023-01-01T00:00:00Z"

    result = google_dataset_metadata(sample_dandiset_metadata)

    # Check that datePublished is preserved
    assert result["datePublished"] == "2023-01-01T00:00:00Z"


def test_google_dataset_metadata_with_date_created_fallback(sample_dandiset_metadata):
    """Test fallback to dateCreated when datePublished is not present"""
    # Add dateCreated field
    sample_dandiset_metadata["dateCreated"] = "2022-01-01T00:00:00Z"

    result = google_dataset_metadata(sample_dandiset_metadata)

    # Check that datePublished is set to dateCreated
    assert result["datePublished"] == "2022-01-01T00:00:00Z"
