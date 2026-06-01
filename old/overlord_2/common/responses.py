# common/responses.py

from typing import Any, Dict, Optional


def api_ok(data: Any = None, message: Optional[str] = None) -> Dict[str, Any]:
    response: Dict[str, Any] = {"status": "ok"}
    if data is not None:
        response["data"] = data
    if message is not None:
        response["message"] = message
    return response


def api_error(message: str, data: Any = None) -> Dict[str, Any]:
    response: Dict[str, Any] = {"status": "error", "message": message}
    if data is not None:
        response["data"] = data
    return response
