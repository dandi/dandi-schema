import json
import logging
from pathlib import Path
from typing import Optional, Union

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
    "instance_identifier": "RRID:ABC_123456",
    "instance_url": "https://dandiarchive.org/",
    "doi_prefix": "10.1234",
    "licenses": ["spdx:AdaCore-doc", "spdx:AGPL-3.0-or-later", "spdx:NBPL-1.0"],
}

# Same as `FOO_CONFIG_DICT` but with the field aliases instead of the field names being
# the keys
FOO_CONFIG_DICT_WITH_ALIASES = {f"dandi_{k}": v for k, v in FOO_CONFIG_DICT.items()}

FOO_CONFIG_ENV_VARS = {
    k: v if k != "licenses" else json.dumps(v) for k, v in FOO_CONFIG_DICT.items()
}


class TestConfig:
    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars", [{}], indirect=True
    )
    @pytest.mark.usefixtures("clear_dandischema_modules_and_set_env_vars")
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

    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars", [{}], indirect=True
    )
    @pytest.mark.usefixtures("clear_dandischema_modules_and_set_env_vars")
    @pytest.mark.parametrize("instance_name", ["-DANDI", "dandi", "DANDI0", "DANDI*"])
    def test_invalid_instance_name(self, instance_name: str) -> None:
        """
        Test instantiating `dandischema.conf.Config` with an invalid instance name
        """
        from dandischema.conf import Config

        with pytest.raises(ValidationError) as exc_info:
            Config(instance_name=instance_name)

        assert len(exc_info.value.errors()) == 1
        assert exc_info.value.errors()[0]["loc"] == ("dandi_instance_name",)

    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars", [{}], indirect=True
    )
    @pytest.mark.usefixtures("clear_dandischema_modules_and_set_env_vars")
    @pytest.mark.parametrize(
        "instance_identifier", [None, "RRID:ABC_123456", "RRID:SCR_1234567891234"]
    )
    def test_valid_instance_identifier(
        self, instance_identifier: Optional[str]
    ) -> None:
        """
        Test instantiating `dandischema.conf.Config` with a valid instance identifier
        """
        from dandischema.conf import Config

        Config(instance_identifier=instance_identifier)

    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars", [{}], indirect=True
    )
    @pytest.mark.usefixtures("clear_dandischema_modules_and_set_env_vars")
    @pytest.mark.parametrize("instance_identifier", ["", "RRID:AB C", "ID:ABC_123456"])
    def test_invalid_instance_identifier(self, instance_identifier: str) -> None:
        """
        Test instantiating `dandischema.conf.Config` with an invalid instance identifier
        """
        from dandischema.conf import Config

        with pytest.raises(ValidationError) as exc_info:
            Config(instance_identifier=instance_identifier)

        assert len(exc_info.value.errors()) == 1
        assert exc_info.value.errors()[0]["loc"] == ("dandi_instance_identifier",)

    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars", [{}], indirect=True
    )
    @pytest.mark.usefixtures("clear_dandischema_modules_and_set_env_vars")
    def test_without_instance_identifier_with_doi_prefix(self) -> None:
        """
        Test instantiating `dandischema.conf.Config` without an instance identifier
        when a DOI prefix is provided
        """
        from dandischema.conf import Config

        with pytest.raises(
            ValidationError, match="`instance_identifier` must also be set."
        ):
            Config(doi_prefix="10.1234")

    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars", [{}], indirect=True
    )
    @pytest.mark.usefixtures("clear_dandischema_modules_and_set_env_vars")
    @pytest.mark.parametrize(
        "doi_prefix", ["10.1234", "10.5678", "10.12345678", "10.987654321"]
    )
    def test_valid_doi_prefix(self, doi_prefix: str) -> None:
        """
        Test instantiating `dandischema.conf.Config` with a valid DOI prefix
        """
        from dandischema.conf import Config

        Config(
            # Instance identifier must be provided if doi_prefix is provided
            instance_identifier="RRID:SCR_017571",
            doi_prefix=doi_prefix,
        )

    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars", [{}], indirect=True
    )
    @pytest.mark.usefixtures("clear_dandischema_modules_and_set_env_vars")
    @pytest.mark.parametrize("doi_prefix", ["1234", ".1234", "1.1234", "10.123"])
    def test_invalid_doi_prefix(self, doi_prefix: str) -> None:
        """
        Test instantiating `dandischema.conf.Config` with an invalid DOI prefix
        """
        from dandischema.conf import Config

        with pytest.raises(ValidationError) as exc_info:
            Config(
                # Instance identifier must be provided if doi_prefix is provided
                instance_identifier="RRID:SCR_017571",
                doi_prefix=doi_prefix,
            )

        assert len(exc_info.value.errors()) == 1
        assert exc_info.value.errors()[0]["loc"] == ("dandi_doi_prefix",)

    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars", [{}], indirect=True
    )
    @pytest.mark.usefixtures("clear_dandischema_modules_and_set_env_vars")
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
        from dandischema.conf import Config, License

        # noinspection PyTypeChecker
        config = Config(licenses=licenses)

        assert config.licenses == {License(license_) for license_ in set(licenses)}

    @pytest.mark.parametrize(
        ("clear_dandischema_modules_and_set_env_vars", "licenses"),
        [
            ({"licenses": "[]"}, set()),
            (
                {"licenses": '["spdx:AGPL-1.0-only"]'},
                {"spdx:AGPL-1.0-only"},
            ),
            (
                {
                    "licenses": '["spdx:AGPL-1.0-only", "spdx:LOOP", "spdx:SPL-1.0", "spdx:LOOP"]'
                },
                {"spdx:AGPL-1.0-only", "spdx:LOOP", "spdx:SPL-1.0", "spdx:LOOP"},
            ),
        ],
        indirect=["clear_dandischema_modules_and_set_env_vars"],
    )
    def test_valid_licenses_by_env_var(
        self, clear_dandischema_modules_and_set_env_vars: None, licenses: set[str]
    ) -> None:
        """
        Test instantiating `dandischema.conf.Config` with a valid array of licenses,
        in JSON format, as an environment variable.
        """
        from dandischema.conf import Config, License

        # noinspection PyTypeChecker
        config = Config()

        assert config.licenses == {License(license_) for license_ in licenses}

    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars", [{}], indirect=True
    )
    @pytest.mark.usefixtures("clear_dandischema_modules_and_set_env_vars")
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
        from dandischema.conf import Config

        with pytest.raises(ValidationError) as exc_info:
            # noinspection PyTypeChecker
            Config(licenses=licenses)

        assert len(exc_info.value.errors()) == 1
        assert exc_info.value.errors()[0]["loc"][:-1] == ("dandi_licenses",)

    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars",
        [
            {},
            {"instance_name": "BAR"},
            {"instance_name": "BAZ", "instance_url": "https://www.example.com/"},
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "config_dict", [FOO_CONFIG_DICT, FOO_CONFIG_DICT_WITH_ALIASES]
    )
    def test_init_by_kwargs(
        self, clear_dandischema_modules_and_set_env_vars: None, config_dict: dict
    ) -> None:
        """
        Test instantiating `Config` using keyword arguments

        The kwargs are expected to override any environment variables
        """
        from dandischema.conf import Config

        config = Config.model_validate(config_dict)
        config_json_dump = config.model_dump(mode="json")

        assert config_json_dump.keys() == FOO_CONFIG_DICT.keys()
        for k, v in FOO_CONFIG_DICT.items():
            if k == "licenses":
                assert sorted(config_json_dump[k]) == sorted(v)
            else:
                assert config_json_dump[k] == v

    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars",
        [
            {},
        ],
        indirect=True,
    )
    def test_init_by_field_names_through_dotenv(
        self,
        clear_dandischema_modules_and_set_env_vars: None,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Test instantiating `Config` using a dotenv file with field names as keys

        The initialization is expected to fail because the proper keys are the aliases
        when using environment variables or dotenv files.
        """
        from dandischema.conf import Config

        dotenv_file_name = "test.env"
        dotenv_file_path = tmp_path / dotenv_file_name

        # Write a dotenv file with a field name as key
        dotenv_file_path.write_text("instance_name=DANDI-TEST")

        monkeypatch.chdir(tmp_path)

        with pytest.raises(ValidationError) as exc_info:
            # noinspection PyArgumentList
            Config(_env_file=dotenv_file_name)

        errors = exc_info.value.errors()
        assert len(errors) == 1

        assert errors[0]["type"] == "extra_forbidden"


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
        [FOO_CONFIG_ENV_VARS],
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
        assert record_tuple[:-1] == ("dandischema.conf", logging.DEBUG)
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
        [FOO_CONFIG_ENV_VARS],
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
        assert record_tuple[:-1] == (
            "dandischema.conf",
            logging.WARNING,
        )
        assert "different value will not have any affect" in record_tuple[2]

        assert get_instance_config() == Config.model_validate(
            new_config_dict
        ), "Configuration values should be set to the new values"
