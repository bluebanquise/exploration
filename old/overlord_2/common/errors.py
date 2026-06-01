# common/errors.py

class PluginError(Exception):
    """Base class for plugin-related errors."""


class ValidationError(PluginError):
    """Invalid input, bad payload, or schema errors."""


class NotFoundError(PluginError):
    """Requested resource was not found."""
