import json
from typing import Union
from unittest.mock import ANY

import pytest
from pydantic import ValidationError

from dandischema.conf import (
    Config,
    License,
    _instance_config,
    get_instance_config,
    set_instance_config,
)


def test_get_instance_config() -> None:
    obtained_config = get_instance_config()

    assert obtained_config == _instance_config
    assert obtained_config is not _instance_config, (
        "`get_instance_config` should return a copy of the instance config"
    )


FOO_CONFIG_DICT = {
    "instance_name": "FOO",
    "doi_prefix": "10.1234",
    "licenses": ["spdx:AdaCore-doc", "spdx:AGPL-3.0-or-later", "spdx:NBPL-1.0"],
}

FOO_CONFIG_ENV_VARS = {
    k: v if k != "licenses" else json.dumps(v) for k, v in FOO_CONFIG_DICT.items()
}


class TestConfig:
    @pytest.mark.parametrize(
        "instance_name",
        ["DANDI-ADHOC", "DANDI-TEST", "DANDI", "DANDI--TEST", "DANDI-TE-ST"],
    )
    def test_valid_instance_name(self, instance_name: str) -> None:
        """
        Test instantiating `dandischema.conf.Config` with a valid instance name
        """
        Config(instance_name=instance_name)

    @pytest.mark.parametrize("instance_name", ["-DANDI", "dandi", "DANDI0", "DANDI*"])
    def test_invalid_instance_name(self, instance_name: str) -> None:
        """
        Test instantiating `dandischema.conf.Config` with an invalid instance name
        """
        with pytest.raises(ValidationError) as exc_info:
            Config(instance_name=instance_name)

        assert len(exc_info.value.errors()) == 1
        assert exc_info.value.errors()[0]["loc"] == ("instance_name",)

    @pytest.mark.parametrize(
        "doi_prefix", ["10.1234", "10.5678", "10.12345678", "10.987654321"]
    )
    def test_valid_doi_prefix(self, doi_prefix: str) -> None:
        """
        Test instantiating `dandischema.conf.Config` with a valid DOI prefix
        """
        Config(doi_prefix=doi_prefix)

    @pytest.mark.parametrize("doi_prefix", ["1234", ".1234", "1.1234", "10.123"])
    def test_invalid_doi_prefix(self, doi_prefix: str) -> None:
        """
        Test instantiating `dandischema.conf.Config` with an invalid DOI prefix
        """
        with pytest.raises(ValidationError) as exc_info:
            Config(doi_prefix=doi_prefix)

        assert len(exc_info.value.errors()) == 1
        assert exc_info.value.errors()[0]["loc"] == ("doi_prefix",)

    @pytest.mark.parametrize(
        "licenses",
        [
            [],
            ["spdx:AGPL-1.0-only"],
            ["spdx:AGPL-1.0-only", "spdx:LOOP", "spdx:SPL-1.0", "spdx:LOOP"],
            set(),
            {"spdx:AGPL-1.0-only"},
            {"spdx:AGPL-1.0-only", "spdx:LOOP", "spdx:SPL-1.0"},
        ],
    )
    def test_valid_licenses_by_args(self, licenses: Union[list[str], set[str]]) -> None:
        """
        Test instantiating `dandischema.conf.Config` with a valid list/set of licenses
        as argument.
        """
        # noinspection PyTypeChecker
        config = Config(licenses=licenses)  # type: ignore

        assert config.licenses == {License(license_) for license_ in set(licenses)}

    @pytest.mark.parametrize(
        ("env_vars", "licenses"),
        [
            ({"DANDI_LICENSES": "[]"}, set()),
            (
                {"DANDI_LICENSES": '["spdx:AGPL-1.0-only"]'},
                {"spdx:AGPL-1.0-only"},
            ),
            (
                {
                    "DANDI_LICENSES": '["spdx:AGPL-1.0-only", "spdx:LOOP", "spdx:SPL-1.0", "spdx:LOOP"]'
                },
                {"spdx:AGPL-1.0-only", "spdx:LOOP", "spdx:SPL-1.0", "spdx:LOOP"},
            ),
        ],
    )
    @pytest.mark.usefixtures("clear_config")
    def test_valid_licenses_by_env_var(
        self, env_vars, licenses: set[str], set_env
    ) -> None:
        """
        Test instantiating `dandischema.conf.Config` with a valid array of licenses,
        in JSON format, as an environment variable.
        """
        with set_env(env_vars):
            # noinspection PyTypeChecker
            config = Config()
            assert config.licenses == {License(license_) for license_ in licenses}

    @pytest.mark.parametrize(
        "licenses",
        [
            {"AGPL-1.0-only"},
            {"spdx:AGPL-1.0-only", "spdx:NOT-A-LICENSE", "spdx:SPL-1.0"},
        ],
    )
    def test_invalid_licenses_by_args(self, licenses: set[str]) -> None:
        """
        Test instantiating `dandischema.conf.Config` with an invalid list/set of
        licenses as an argument
        """
        with pytest.raises(ValidationError) as exc_info:
            # noinspection PyTypeChecker
            Config(licenses=licenses)  # type: ignore

        assert len(exc_info.value.errors()) == 1
        assert exc_info.value.errors()[0]["loc"] == ("licenses", ANY)


class TestSetInstanceConfig:
    @pytest.mark.parametrize(
        ("arg", "kwargs"),
        [
            (FOO_CONFIG_DICT, {"instance_name": "BAR"}),
            (
                FOO_CONFIG_DICT,
                {"instance_name": "Baz", "key": "value"},
            ),
        ],
    )
    def test_invalid_args(self, arg: dict, kwargs: dict) -> None:
        """
        Test that `set_instance_config` raises a `ValueError` when called with both
        a non-none positional argument and one or more keyword arguments.
        """

        # Loop over arg in different types/forms
        for arg_ in (arg, Config.model_validate(arg)):
            with pytest.raises(ValueError, match="not both"):
                set_instance_config(arg_, **kwargs)
