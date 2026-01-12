# common/errors.py

class PluginError(Exception):
    """Base class for all plugin-related errors."""


class ValidationError(PluginError):
    """Invalid input, malformed payload, or user error."""


class NotFoundError(PluginError):
    """Requested resource does not exist."""


class ConflictError(PluginError):
    """Resource exists or operation cannot be completed due to conflict."""


class PermissionError(PluginError):
    """User is not allowed to perform this action (future use)."""
