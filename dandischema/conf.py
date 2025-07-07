# This file defines the configuration for the DANDI schema

from __future__ import annotations

import logging
import re
from typing import Annotated, Any, Optional

from pydantic import StringConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict

_MODELS_MODULE_NAME = "dandischema.models"
"""The full import name of the module containing the DANDI Pydantic models"""

_UNVENDORED_ID_PATTERN = r"[A-Z][-A-Z]*"
_UNVENDORED_DOI_PREFIX_PATTERN = r"10\.\d{4,}"

logger = logging.getLogger(__name__)


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

    @property
    def id_pattern(self) -> str:
        """Regex pattern for the prefix of identifiers"""
        if "instance_name" in self.model_fields_set:
            return self.instance_name

        # If the instance name is not set,
        #   we use a pattern for unvendored DANDI instances
        return _UNVENDORED_ID_PATTERN

    @property
    def doi_prefix_pattern(self) -> Optional[str]:
        """The pattern that a DOI prefix of a dandiset must conform to"""
        return re.escape(self.doi_prefix) if self.doi_prefix is not None else None


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


def set_instance_config(**kwargs: Any) -> None:
    """
    Set the DANDI instance configuration returned by `get_instance_config()`

    This setting is done by creating a new instance of `Config` with the keyword
    arguments passed to this function and overwriting the existing one.

    Parameters
    ----------
    **kwargs
        Keyword arguments to pass to the `Config` constructor

    Note
    ----
        Use this function to override the initial configuration set by the environment
        variables.

        This function should be called before importing `dandischema.models` or the
        new configuration will not have any affect in the models defined in
        `dandischema.models`.

    """
    import sys

    global _instance_config

    new_config = Config(**kwargs)

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
