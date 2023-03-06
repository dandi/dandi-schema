from typing import Any, Dict, List

import jsonschema.exceptions


class ValidationError(ValueError):
    pass


class JsonschemaValidationError(ValidationError):
    """Validation errors were detected by jsonschema"""

    def __init__(self, errors: List[jsonschema.exceptions.ValidationError]) -> None:
        self.errors = errors


class PydanticValidationError(ValidationError):
    """Validation errors were detected by pydantic"""

    def __init__(self, errors: List[Dict[str, Any]]) -> None:
        self.errors = errors
