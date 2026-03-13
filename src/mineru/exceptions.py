from __future__ import annotations


class MinerUError(Exception):
    """Base exception for all MinerU SDK errors."""

    def __init__(self, code: str | int, message: str, *, trace_id: str = "") -> None:
        self.code = str(code)
        self.message = message
        self.trace_id = trace_id
        tag = f" (trace: {trace_id})" if trace_id else ""
        super().__init__(f"[{self.code}] {message}{tag}")


class AuthError(MinerUError):
    """Token is invalid or expired (A0202, A0211)."""


class ParamError(MinerUError):
    """Request parameter error (-500, -10002)."""


class FileTooLargeError(MinerUError):
    """File exceeds 200 MB limit (-60005)."""


class PageLimitError(MinerUError):
    """File exceeds 600 page limit (-60006)."""


class TaskNotFoundError(MinerUError):
    """task_id is invalid or deleted (-60012)."""


class ExtractFailedError(MinerUError):
    """Extraction failed on the server side (-60010)."""


class TimeoutError(MinerUError):
    """SDK-side timeout waiting for task completion."""

    def __init__(self, timeout: int, task_id: str) -> None:
        super().__init__("TIMEOUT", f"Task {task_id} did not complete within {timeout}s")
        self.timeout = timeout
        self.task_id = task_id


class QuotaExceededError(MinerUError):
    """Daily parsing quota exhausted (-60018, -60019)."""


_CODE_TO_EXCEPTION: dict[str, type[MinerUError]] = {
    "A0202": AuthError,
    "A0211": AuthError,
    "-500": ParamError,
    "-10002": ParamError,
    "-60005": FileTooLargeError,
    "-60006": PageLimitError,
    "-60010": ExtractFailedError,
    "-60012": TaskNotFoundError,
    "-60013": MinerUError,
    "-60018": QuotaExceededError,
    "-60019": QuotaExceededError,
}


def raise_for_code(code: int | str, msg: str, trace_id: str = "") -> None:
    """Raise the appropriate exception for an API error code."""
    key = str(code)
    exc_cls = _CODE_TO_EXCEPTION.get(key, MinerUError)
    raise exc_cls(code, msg, trace_id=trace_id)
