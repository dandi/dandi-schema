import os
from typing import Iterator

import pytest


@pytest.fixture(scope="session", autouse=True)
def disable_http() -> Iterator[None]:
    if os.environ.get("DANDI_TESTS_NONETWORK"):
        with pytest.MonkeyPatch().context() as m:
            m.setenv("http_proxy", "http://127.0.0.1:9/")
            m.setenv("https_proxy", "http://127.0.0.1:9/")
            yield
    else:
        yield
