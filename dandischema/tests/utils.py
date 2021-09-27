import os

import pytest

skipif_no_network = pytest.mark.skipif(
    os.environ.get("DANDI_TESTS_NONETWORK"), reason="no network settings"
)
