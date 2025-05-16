# This file defines the configuration for the DANDI schema

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    id_pattern: str = r"[A-Z]+"
    """Regex pattern for the prefix of identifiers"""

    datacite_doi_id_pattern: str = r"\d{4,}"
    """
    The registrant code pattern of the DOI prefix at DataCite

    The number sequence that follows "10." within the DOI prefix as documented
    at https://support.datacite.org/docs/prefixes.
    """


CONFIG = Config()
