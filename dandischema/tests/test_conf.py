import logging
from unittest.mock import ANY

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


class TestSetInstanceConfig:

    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars",
        [{}],
        indirect=True,
    )
    def test_before_models_import(
        self, clear_dandischema_modules_and_set_env_vars: None
    ) -> None:
        """
        Test setting the instance configuration before importing `dandischema.models`.
        """

        # Import entities in `dandischema.conf` after clearing dandischema modules
        from dandischema.conf import Config, get_instance_config, set_instance_config

        set_instance_config(**FOO_CONFIG_DICT)
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
        # Make sure the `dandischema.models` module is imported before calling
        # `set_instance_config`
        from dandischema.conf import Config, get_instance_config, set_instance_config
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
        # Make sure the `dandischema.models` module is imported before calling
        # `set_instance_config`
        from dandischema.conf import Config, get_instance_config, set_instance_config
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
