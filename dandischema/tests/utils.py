from datetime import datetime
import os
from typing import Any, Dict

import pytest

skipif_no_network = pytest.mark.skipif(
    bool(os.environ.get("DANDI_TESTS_NONETWORK")), reason="no network settings"
)


def _basic_publishmeta(
    dandi_id: str, version: str = "0.0.0", prefix: str = "10.80507"
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
                    "version": version,
                    "schemaKey": "Software",
                }
            ],
            "schemaKey": "PublishActivity",
        },
        "version": version,
        "doi": f"{prefix}/dandi.{dandi_id}/{version}",
    }
    return publish_meta
