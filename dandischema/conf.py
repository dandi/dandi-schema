# This file defines the configuration for the DANDI schema

from __future__ import annotations

from typing import Annotated, Optional

from pydantic import StringConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict

_UNVENDORED_ID_PATTERN = r"[A-Z][-A-Z]*"
_UNVENDORED_DATACITE_DOI_ID_PATTERN = r"\d{4,}"


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

    datacite_doi_id: Optional[
        Annotated[
            str, StringConstraints(pattern=rf"^{_UNVENDORED_DATACITE_DOI_ID_PATTERN}$")
        ]
    ] = None
    """
    The registrant code of the DOI prefix at DataCite

    The number sequence that follows "10." within the DOI prefix as documented
    at https://support.datacite.org/docs/prefixes.
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
    def datacite_doi_id_pattern(self) -> Optional[str]:
        """The registrant code pattern of the DOI prefix at DataCite"""
        return self.datacite_doi_id


CONFIG = Config()
