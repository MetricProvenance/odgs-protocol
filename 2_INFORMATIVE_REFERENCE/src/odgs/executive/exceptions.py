class ProcessBlockedException(Exception):
    """Raised when a Process is blocked by a Rule Violation (Hard Stop)."""
    pass


class SoftStopException(ProcessBlockedException):
    """Raised when a SOFT_STOP rule fails and no override token is provided.

    SOFT_STOP is an overrideable block: it halts the pipeline by default,
    but an authorized caller can supply a cryptographic override token to
    proceed.  The override is always logged in the S-Cert audit entry.
    """
    def __init__(self, message: str, rule_id: str = None):
        super().__init__(message)
        self.rule_id = rule_id


class MissingRuleException(ProcessBlockedException):
    """Raised when a required Sovereign Definition or Rule is absent."""
    def __init__(self, message: str, status_code: int = 428):
        super().__init__(message)
        self.status_code = status_code


class DependencyFailedException(ProcessBlockedException):
    """Raised when a rule's dependency failed, so this rule cannot execute."""
    def __init__(self, message: str, rule_id: str = None, failed_dependency: str = None):
        super().__init__(message)
        self.rule_id = rule_id
        self.failed_dependency = failed_dependency


class SchemaValidationException(Exception):
    """Raised when a custom JSON blueprint fails core schema validation."""
    pass


class ConformanceException(Exception):
    """Raised when the ODGS project fails a conformance self-check."""
    def __init__(self, message: str, level: str = "L1", failures: list = None):
        super().__init__(message)
        self.level = level
        self.failures = failures or []
