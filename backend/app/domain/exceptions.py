class DomainError(Exception):
    pass


class NotFound(DomainError):
    pass


class Unauthorized(DomainError):
    pass


class Forbidden(DomainError):
    pass


class Conflict(DomainError):
    pass


class UploadRejected(DomainError):
    def __init__(self, *, reason_code: str, detail: str, status_code: int = 422) -> None:
        super().__init__(detail)
        self.reason_code = reason_code
        self.detail = detail
        self.status_code = status_code


class ServiceUnavailable(DomainError):
    def __init__(self, *, reason_code: str, detail: str, status_code: int = 503) -> None:
        super().__init__(detail)
        self.reason_code = reason_code
        self.detail = detail
        self.status_code = status_code
