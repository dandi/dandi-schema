import os

import pytest

skipif_no_network = pytest.mark.skipif(
    bool(os.environ.get("DANDI_TESTS_NONETWORK")), reason="no network settings"
)
