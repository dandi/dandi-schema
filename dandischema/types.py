# This file is for defining types that extend existing types through the use of
# `typing.Annotated`.

from typing import Annotated, Type

from pydantic import ByteSize, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema


class _ByteSizeJsonSchemaAnnotation:
    """
    An annotation for `pydantic.ByteSize` that provides a JSON schema

    Note: Pydantic V2 doesn't provide a JSON schema for `pydantic.ByteSize`.
          This annotation provides a JSON schema that is the same JSON schema
          used for `pydantic.ByteSize` in Pydantic V1, which is simply the JSON
          schema for `int`.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Type[ByteSize], handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        assert source is ByteSize
        return handler(source)

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _core_schema: CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        return handler(core_schema.int_schema())


# An extension of `pydantic.ByteSize` that uses the JSON schema provided by
# `_ByteSizeJsonSchemaAnnotation`
ByteSizeJsonSchema = Annotated[ByteSize, _ByteSizeJsonSchemaAnnotation()]
