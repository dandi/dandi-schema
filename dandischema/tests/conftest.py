import contextlib
import os
from typing import Iterator

import pytest

from dandischema.conf import get_instance_config, set_instance_config


@pytest.fixture(scope="session", autouse=True)
def disable_http() -> Iterator[None]:
    if os.environ.get("DANDI_TESTS_NONETWORK"):
        with pytest.MonkeyPatch().context() as m:
            m.setenv("http_proxy", "http://127.0.0.1:9/")
            m.setenv("https_proxy", "http://127.0.0.1:9/")
            yield
    else:
        yield


@pytest.fixture()
def clear_config():
    """Clear instance config before each test."""
    config = get_instance_config()

    set_instance_config(None)
    yield

    set_instance_config(config)


@pytest.fixture()
def set_env():
    @contextlib.contextmanager
    def env_setter(env_vars: dict[str, str]):
        old_env = os.environ.copy()
        os.environ.update(env_vars)

        try:
            yield
        finally:
            for key in env_vars.keys():
                old_val = old_env.get(key, None)
                if old_val is None:
                    os.environ.pop(key)
                else:
                    os.environ[key] = old_val

    return env_setter
