# This file defines the configuration for the DANDI schema

from __future__ import annotations

from datetime import datetime
from enum import Enum
from importlib.resources import files
import logging
from typing import TYPE_CHECKING, Annotated, Any, Optional, Union

from pydantic import AnyUrl, BaseModel, Field, StringConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict

_MODELS_MODULE_NAME = "dandischema.models"
"""The full import name of the module containing the DANDI Pydantic models"""

_UNVENDORED_ID_PATTERN = r"[A-Z][-A-Z]*"
_UNVENDORED_DOI_PREFIX_PATTERN = r"10\.\d{4,}"

logger = logging.getLogger(__name__)


class SpdxLicenseListInfo(BaseModel):
    """
    Represents information about the SPDX License List.
    """

    version: str
    release_date: datetime
    url: AnyUrl
    reference: AnyUrl = AnyUrl("https://spdx.org/licenses/")


class SpdxLicenseIdList(BaseModel):
    """
    Represents a list of SPDX license IDs.
    """

    source: SpdxLicenseListInfo
    license_ids: list[str]


license_id_file_path = files(__package__) / "_resources" / "spdx_license_ids.json"

spdx_license_id_list = SpdxLicenseIdList.model_validate_json(
    license_id_file_path.read_text()
)

if TYPE_CHECKING:
    # This is just a placeholder for static type checking
    class License(Enum):
        ...  # fmt: skip

else:
    License = Enum(
        "License",
        [("spdx:" + id_,) * 2 for id_ in spdx_license_id_list.license_ids],
    )


class Config(BaseSettings):
    """
    Configuration for the DANDI schema

    Note
    ----
        Since this class is subclass of `pydantic.BaseSettings`, each field of an
        instance of this class can be populated from an environment variable of the
        same name prefixed with the prefix defined in `model_config` with the name
        of the environment variable interpreted **case-insensitively**.
        For details, see https://docs.pydantic.dev/latest/concepts/pydantic_settings/
    """

    model_config = SettingsConfigDict(env_prefix="dandi_")

    instance_name: Annotated[
        str, StringConstraints(pattern=rf"^{_UNVENDORED_ID_PATTERN}$")
    ] = "DANDI-ADHOC"
    """Name of the DANDI instance"""

    doi_prefix: Optional[
        Annotated[
            str, StringConstraints(pattern=rf"^{_UNVENDORED_DOI_PREFIX_PATTERN}$")
        ]
    ] = None
    """
    The DOI prefix at DataCite
    """

    licenses: set[License] = Field(
        default={License("spdx:CC0-1.0"), License("spdx:CC-BY-4.0")}
    )
    """
    Set of licenses to be supported by the DANDI instance

    Currently, the values for this set must be the identifier of a license in the
    list at https://spdx.org/licenses/ prefixed with "spdx:" when set with the
    corresponding environment variable. E.g.

    ```shell
    export DANDI_LICENSES='["spdx:CC0-1.0", "spdx:CC-BY-4.0"]'
    ```
    """


_instance_config = Config()  # Initial value is set by env vars alone
"""
Configuration of the DANDI instance

This configuration holds the information used to customize the DANDI schema to a
specific vendor, but it should not be accessed directly. Use `get_instance_config()`
to obtain its value and `set_instance_config()` to set its value.
"""


def get_instance_config() -> Config:
    """
    Get the configuration of the DANDI instance

    This configuration holds the information used to customize the DANDI schema to a
    specific vendor.

    Returns
    -------
    Config
        The configuration of the DANDI instance
    """
    return _instance_config.model_copy(deep=True)


def set_instance_config(
    config: Optional[Union[Config, dict]] = None, /, **kwargs: Any
) -> None:
    """
    Set the DANDI instance configuration returned by `get_instance_config()`

    This setting is done by creating a new instance of `Config` with the positional
    argument of type of `Config` or `dict` or the keyword
    arguments passed to this function and overwriting the existing one.

    Parameters
    ----------
    config : Optional[Union[Config, dict]], optional
        An instance of `Config` or a dictionary with the configuration. If an instance
        of `Config` is provided, a copy will be made to use to set the DANDI instance
        configuration. If a dictionary is provided, it will be validated and converted
        to an instance of `Config`. If this argument is provided, no keyword arguments
        should be provided. Defaults to `None`.
    **kwargs
        Keyword arguments to pass to `Config.model_validate()` to create a new
        instance of `Config` to set the DANDI instance configuration.

    Raises
    ------
    ValueError
        If both a non-none positional argument and keyword arguments are provided

    Note
    ----
        Use this function to override the initial configuration set by the environment
        variables.

        This function should be called before importing `dandischema.models` or the
        new configuration will not have any affect in the models defined in
        `dandischema.models`.

    """
    if config is not None and kwargs:
        raise ValueError(
            "Either a positional argument or a set of keyword arguments should be "
            "provided, but not both."
        )

    import sys

    global _instance_config

    if config is not None:
        if isinstance(config, Config):
            new_config = config.model_copy(deep=True)
        else:
            new_config = Config.model_validate(config)
    else:
        new_config = Config.model_validate(kwargs)

    if _MODELS_MODULE_NAME in sys.modules:
        if new_config != _instance_config:
            logger.warning(
                f"`{_MODELS_MODULE_NAME}` is already imported. Resetting the DANDI "
                f"instance configuration to a different value will not have any affect "
                f"in the models defined in `{_MODELS_MODULE_NAME}`."
            )
        else:
            logger.debug(
                f"`{_MODELS_MODULE_NAME}` is already imported. Attempt to "
                f"reset the DANDI instance configuration to the same value by "
                f"keyword argument has been ignored."
            )
            return

    _instance_config = new_config
