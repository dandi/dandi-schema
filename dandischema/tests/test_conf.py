import logging
from typing import Optional
from unittest.mock import ANY

from pydantic import ValidationError
import pytest


def test_get_instance_config() -> None:
    from dandischema.conf import _instance_config, get_instance_config

    obtained_config = get_instance_config()

    assert obtained_config == _instance_config
    assert (
        obtained_config is not _instance_config
    ), "`get_instance_config` should return a copy of the instance config"


FOO_CONFIG_DICT = {
    "instance_name": "FOO",
    "doi_prefix": "10.1234",
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
        from dandischema.conf import Config

        Config(instance_name=instance_name)

    @pytest.mark.parametrize("instance_name", ["-DANDI", "dandi", "DANDI0", "DANDI*"])
    def test_invalid_instance_name(self, instance_name: str) -> None:
        """
        Test instantiating `dandischema.conf.Config` with an invalid instance name
        """
        from dandischema.conf import Config

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
        from dandischema.conf import Config

        Config(doi_prefix=doi_prefix)

    @pytest.mark.parametrize("doi_prefix", ["1234", ".1234", "1.1234", "10.123"])
    def test_invalid_doi_prefix(self, doi_prefix: str) -> None:
        """
        Test instantiating `dandischema.conf.Config` with an invalid DOI prefix
        """
        from dandischema.conf import Config

        with pytest.raises(ValidationError) as exc_info:
            Config(doi_prefix=doi_prefix)

        assert len(exc_info.value.errors()) == 1
        assert exc_info.value.errors()[0]["loc"] == ("doi_prefix",)


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
        from dandischema.conf import Config, set_instance_config

        # Loop over arg in different types/forms
        for arg_ in (arg, Config.model_validate(arg)):
            with pytest.raises(ValueError, match="not both"):
                set_instance_config(arg_, **kwargs)

    @pytest.mark.parametrize(
        ("clear_dandischema_modules_and_set_env_vars", "arg", "kwargs"),
        [
            ({}, FOO_CONFIG_DICT, {}),
            ({}, FOO_CONFIG_DICT, {}),
            ({}, None, FOO_CONFIG_DICT),
        ],
        indirect=["clear_dandischema_modules_and_set_env_vars"],
    )
    def test_before_models_import(
        self,
        clear_dandischema_modules_and_set_env_vars: None,
        arg: Optional[dict],
        kwargs: dict,
    ) -> None:
        """
        Test setting the instance configuration before importing `dandischema.models`.
        """

        # Import entities in `dandischema.conf` after clearing dandischema modules
        from dandischema.conf import Config, get_instance_config, set_instance_config

        # Loop over arg in different types/forms
        for arg_ in (arg, Config.model_validate(arg)) if arg is not None else (arg,):
            set_instance_config(arg_, **kwargs)
            assert get_instance_config() == Config.model_validate(
                FOO_CONFIG_DICT
            ), "Configuration values are not set to the expected values"

    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars",
        [FOO_CONFIG_DICT],
        indirect=True,
    )
    def test_after_models_import_same_config(
        self,
        clear_dandischema_modules_and_set_env_vars: None,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """
        Test setting the instance configuration after importing `dandischema.models`
        with the same configuration.
        """
        from dandischema.conf import Config, get_instance_config, set_instance_config

        # Make sure the `dandischema.models` module is imported before calling
        # `set_instance_config`
        import dandischema.models  # noqa: F401

        initial_config = get_instance_config()

        caplog.clear()
        caplog.set_level(logging.DEBUG, logger="dandischema.conf")
        set_instance_config(**FOO_CONFIG_DICT)

        assert (
            len(caplog.records) == 1
        ), "There should be only one log record from logger `dandischema.conf`"

        record_tuple = caplog.record_tuples[0]
        assert record_tuple == ("dandischema.conf", logging.DEBUG, ANY)
        assert (
            "reset the DANDI instance configuration to the same value"
            in record_tuple[2]
        )

        assert (
            get_instance_config()
            == initial_config
            == Config.model_validate(FOO_CONFIG_DICT)
        ), "Configuration values should remain the same"

    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars",
        [FOO_CONFIG_DICT],
        indirect=True,
    )
    def test_after_models_import_different_config(
        self,
        clear_dandischema_modules_and_set_env_vars: None,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """
        Test setting the instance configuration after importing `dandischema.models`
        with a different configuration.
        """
        from dandischema.conf import Config, get_instance_config, set_instance_config

        # Make sure the `dandischema.models` module is imported before calling
        # `set_instance_config`
        import dandischema.models  # noqa: F401

        new_config_dict = {
            "instance_name": "BAR",
            "doi_prefix": "10.5678",
        }

        # noinspection DuplicatedCode
        caplog.clear()
        caplog.set_level(logging.DEBUG, logger="dandischema.conf")
        set_instance_config(**new_config_dict)

        assert (
            len(caplog.records) == 1
        ), "There should be only one log record from logger `dandischema.conf`"
        record_tuple = caplog.record_tuples[0]
        assert record_tuple == ("dandischema.conf", logging.WARNING, ANY)
        assert "different value will not have any affect" in record_tuple[2]

        assert get_instance_config() == Config.model_validate(
            new_config_dict
        ), "Configuration values should be set to the new values"
