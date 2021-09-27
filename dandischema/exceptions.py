class JsonschemaValidationError(ValueError):
    """Validation errors were detected by jsonschema.

    All errors are contained in the .args[0] of the exception instance.
    """
    @property
    def errors(self):
        return self.args[0]


class PydanticValidationError(ValueError):
    """Validation errors were detected by pydantic.

    All errors are contained in the .args[0] of the exception instance.
    """
    @property
    def errors(self):
        return self.args[0]
