from typing import Any, Dict, List
import jsonschema.exceptions


class ValidationError(ValueError):
    pass


class JsonschemaValidationError(ValidationError):
    """Validation errors were detected by jsonschema.

    All errors are contained in the .args[0] of the exception instance.
    """
    @property
    def errors(self) -> List[jsonschema.exceptions.ValidationError]:
        return self.args[0]


class PydanticValidationError(ValidationError):
    """Validation errors were detected by pydantic.

    All errors are contained in the .args[0] of the exception instance.
    """
    @property
    def errors(self) -> List[Dict[str, Any]]:
        return self.args[0]
