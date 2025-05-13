from datetime import datetime
import os
from pathlib import Path
from typing import Any, Dict

import pytest

from dandischema.conf import CONFIG

if CONFIG.instance_name not in ["DANDI", "DANDI-ADHOC", "EMBER-DANDI"]:
    # This should never happen
    raise NotImplementedError(
        f"There is no testing `Dandiset` metadata for a DANDI"
        f"instance named {CONFIG.instance_name}"
    )

INSTANCE_NAME = CONFIG.instance_name
METADATA_DIR = Path(__file__).with_name("data") / "metadata"
DANDISET_METADATA_DIR = METADATA_DIR / INSTANCE_NAME

DOI_PREFIX = f"10.{DATACITE_DOI_ID}" if DATACITE_DOI_ID is not None else None


skipif_no_network = pytest.mark.skipif(
    bool(os.environ.get("DANDI_TESTS_NONETWORK")), reason="no network settings"
)


skipif_instance_name_not_dandi = pytest.mark.skipif(
    INSTANCE_NAME != "DANDI", reason='The DANDI instance\'s name is not "DANDI"'
)


def _basic_publishmeta(
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
