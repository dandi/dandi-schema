from __future__ import annotations

import re
import sys
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any, ClassVar, Literal, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer,
)

metamodel_version = "1.7.0"
version = "None"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias=True,
        validate_by_name=True,
        validate_assignment=True,
        validate_default=True,
        extra="forbid",
        arbitrary_types_allowed=True,
        use_enum_values=True,
        strict=False,
    )


class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key: str):
        return getattr(self.root, key)

    def __getitem__(self, key: str):
        return self.root[key]

    def __setitem__(self, key: str, value):
        self.root[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.root


linkml_meta = LinkMLMeta(
    {
        "default_prefix": "ex",
        "default_range": "string",
        "id": "https://example.org/dandi-schema-experiment",
        "imports": ["linkml:types"],
        "name": "dandi-schema-experiment",
        "prefixes": {
            "ex": {"prefix_prefix": "ex", "prefix_reference": "https://example.org/dandi-schema-experiment/"},
            "linkml": {"prefix_prefix": "linkml", "prefix_reference": "https://w3id.org/linkml/"},
        },
        "source_file": "schema_no_type_designator.yaml",
    }
)


class DandiBaseModel(ConfiguredBaseModel):
    """
    A base model for Dandi schema.
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://example.org/dandi-schema-experiment",
            "slot_usage": {"schemaKey": {"ifabsent": "string(DandiBaseModel)", "name": "schemaKey"}},
        }
    )

    schemaKey: Optional[str] = Field(
        default="DandiBaseModel",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"], "ifabsent": "string(DandiBaseModel)"}},
    )


class Activity(DandiBaseModel):
    """
    A base activity.
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://example.org/dandi-schema-experiment",
            "slot_usage": {"schemaKey": {"ifabsent": "string(Activity)", "name": "schemaKey"}},
        }
    )

    schemaKey: Optional[str] = Field(
        default="Activity",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"], "ifabsent": "string(Activity)"}},
    )


class Project(Activity):
    """
    A project, which is a kind of activity.
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://example.org/dandi-schema-experiment",
            "slot_usage": {"schemaKey": {"ifabsent": "string(Project)", "name": "schemaKey"}},
        }
    )

    project_name: Optional[str] = Field(default=None, json_schema_extra={"linkml_meta": {"domain_of": ["Project"]}})
    schemaKey: Optional[str] = Field(
        default="Project",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"], "ifabsent": "string(Project)"}},
    )


class CommonModel(DandiBaseModel):
    """
    A base model carrying common slots.
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://example.org/dandi-schema-experiment",
            "slot_usage": {"schemaKey": {"ifabsent": "string(CommonModel)", "name": "schemaKey"}},
        }
    )

    wasGeneratedBy: Optional[list[Activity]] = Field(
        default=None, json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}}
    )
    schemaKey: Optional[str] = Field(
        default="CommonModel",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"], "ifabsent": "string(CommonModel)"}},
    )


class BareAsset(CommonModel):
    """
    An asset, which is a kind of common model.
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://example.org/dandi-schema-experiment",
            "slot_usage": {"schemaKey": {"ifabsent": "string(BareAsset)", "name": "schemaKey"}},
        }
    )

    wasGeneratedBy: Optional[list[Activity]] = Field(
        default=None, json_schema_extra={"linkml_meta": {"domain_of": ["CommonModel"]}}
    )
    schemaKey: Optional[str] = Field(
        default="BareAsset",
        json_schema_extra={"linkml_meta": {"domain_of": ["DandiBaseModel"], "ifabsent": "string(BareAsset)"}},
    )


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
DandiBaseModel.model_rebuild()
Activity.model_rebuild()
Project.model_rebuild()
CommonModel.model_rebuild()
BareAsset.model_rebuild()
