import os
import sys
from typing import Generator, Iterator

from pydantic import ConfigDict, TypeAdapter, ValidationError
import pytest
from typing_extensions import TypedDict

from dandischema.conf import Config


@pytest.fixture(scope="session", autouse=True)
def disable_http() -> Iterator[None]:
    if os.environ.get("DANDI_TESTS_NONETWORK"):
        with pytest.MonkeyPatch().context() as m:
            m.setenv("http_proxy", "http://127.0.0.1:9/")
            m.setenv("https_proxy", "http://127.0.0.1:9/")
            yield
    else:
        yield


_CONFIG_PARAMS = list(Config.model_fields)
"""Configuration parameters of the `dandischema` package"""
# noinspection PyTypedDict
_ENV_DICT = TypedDict(  # type: ignore[misc]
    "_ENV_DICT", {fname: str for fname in _CONFIG_PARAMS}, total=False
)
_ENV_DICT.__pydantic_config__ = ConfigDict(  # type: ignore[attr-defined]
    # Values have to be strictly of type `str`
    strict=True,
    # Keys not listed are not allowed
    extra="forbid",
)
_ENV_DICT_ADAPTER = TypeAdapter(_ENV_DICT)


@pytest.fixture
def clear_dandischema_modules_and_set_env_vars(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> Generator[None, None, None]:
    """
    This fixture clears all `dandischema` modules from `sys.modules` and sets
    environment variables that configure the `dandischema` package.

    With this fixture, tests can import `dandischema` modules cleanly in an environment
    defined by the provided values for the environment variables.

    This fixture expects values for the environment variables to be passed indirectly
    from the calling test function using `request.param`. `request.param` should be a
    `dict[str, str]` consisting of keys that are a subset of the fields of
    `dandischema.conf.Config`. Each value in the dictionary will be used to set an
    environment variable with a name that is the same as its key but in upper case and
    prefixed with "DANDI_".

    Example usage:
    ```python
    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars",
        [
            {},
            {
                "instance_name": "DANDI",
                "datacite_doi_id": "48324",
            },
            {
                "instance_name": "EMBER-DANDI",
                "datacite_doi_id": "60533",
            }
        ],
        indirect=True,
    )
    def test_foo(clear_dandischema_modules_and_set_env_vars):
        # Your test code here
        ...
    ```

    Note
    ----
    When this fixture is torn down, it restores the original `sys.modules` and undo
    the environment variable changes made.

    The user of this fixture needs to ensure that no other threads besides a calling
    thread of this fixture are modifying `sys.modules` during the execution of this
    fixture, which should be a common situation.
    """
    # Check if the calling test has passed valid `indirect` arguments
    ev = ValueError(
        "The calling test must use the `indirect` parameter to pass "
        "a `dict[str, str]` for setting environment variables."
    )
    if not hasattr(request, "param"):
        raise ev
    try:
        _ENV_DICT_ADAPTER.validate_python(request.param)
    except ValidationError as e:
        raise ev from e

    modules = sys.modules
    modules_original = modules.copy()

    # Remove all dandischema modules from sys.modules
    for name in list(modules):
        if name.startswith("dandischema.") or name == "dandischema":
            del modules[name]

    # Monkey patch environment variables with arguments from the calling test
    for p in _CONFIG_PARAMS:
        if p in request.param:
            monkeypatch.setenv(f"DANDI_{p.upper()}", request.param[p])
        else:
            monkeypatch.delenv(f"DANDI_{p.upper()}", raising=False)

    yield

    # Restore the original modules
    for name in list(modules):
        if name not in modules_original:
            del modules[name]
    modules.update(modules_original)
