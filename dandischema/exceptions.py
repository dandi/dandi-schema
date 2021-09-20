class ValidationError(ValueError):
    """Validation errors were detected.

    All errors are contained in the .args[0] of the exception instance.
    """

    @property
    def errors(self):
        return self.args[0]
