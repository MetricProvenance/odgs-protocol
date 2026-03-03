class ProcessBlockedException(Exception):
    """Raised when a Process is blocked by a Rule Violation (Hard Stop)."""
    pass

class MissingRuleException(ProcessBlockedException):
    """Raised when a required Sovereign Definition or Rule is absent."""
    def __init__(self, message: str, status_code: int = 428):
        super().__init__(message)
        self.status_code = status_code

class SchemaValidationException(Exception):
    """Raised when a custom JSON blueprint fails core schema validation."""
    pass
