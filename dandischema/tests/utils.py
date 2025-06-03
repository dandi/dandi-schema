from datetime import datetime
import os
from pathlib import Path
from typing import Any, Dict

import pytest

from dandischema.conf import INSTANCE_CONFIG

INSTANCE_NAME = INSTANCE_CONFIG.instance_name
DATACITE_DOI_ID = INSTANCE_CONFIG.datacite_doi_id

METADATA_DIR = Path(__file__).with_name("data") / "metadata"
DANDISET_METADATA_DIR = METADATA_DIR / INSTANCE_NAME

DOI_PREFIX = f"10.{DATACITE_DOI_ID}" if DATACITE_DOI_ID is not None else None


skipif_no_datacite_auth = pytest.mark.skipif(
    os.getenv("DATACITE_DEV_LOGIN") is None
    or os.getenv("DATACITE_DEV_PASSWORD") is None,
    reason="no datacite login or password set in environment variables",
)

skipif_no_doi_prefix = pytest.mark.skipif(
    DOI_PREFIX is None, reason="DOI_PREFIX is not set"
)

skipif_no_network = pytest.mark.skipif(
    bool(os.environ.get("DANDI_TESTS_NONETWORK")), reason="no network settings"
)

skipif_no_test_dandiset_metadata_dir = pytest.mark.skipif(
    not DANDISET_METADATA_DIR.is_dir(),
    reason=f"No test Dandiset metadata directory for a DANDI instance named "
    f"{INSTANCE_NAME} exists",
)


skipif_instance_name_not_dandi = pytest.mark.skipif(
    INSTANCE_NAME != "DANDI", reason='The DANDI instance\'s name is not "DANDI"'
)


def basic_publishmeta(
    instance_name: str, dandi_id: str, version: str = "0.0.0", prefix: str = "10.80507"
) -> Dict[str, Any]:
    """Return extra metadata required by PublishedDandiset

    Returned fields are additional to fields required by Dandiset
    """
    publish_meta = {
        "datePublished": str(datetime.now().year),
        "publishedBy": {
            "id": "urn:uuid:08fffc59-9f1b-44d6-8e02-6729d266d1b6",
            "name": "DANDI publish",
            "startDate": "2021-05-18T19:58:39.310338-04:00",
            "endDate": "2021-05-18T19:58:39.310361-04:00",
            "wasAssociatedWith": [
                {
                    "id": "urn:uuid:9267d2e1-4a37-463b-9b10-dad3c66d8eaa",
                    "identifier": "RRID:SCR_017571",
                    "name": "DANDI API",
                    "version": "0.1.0",
                    "schemaKey": "Software",
                }
            ],
            "schemaKey": "PublishActivity",
        },
        "version": version,
        "doi": f"{prefix}/{instance_name.lower()}.{dandi_id}/{version}",
    }
    return publish_meta
