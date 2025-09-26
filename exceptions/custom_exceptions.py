from fastapi.exceptions import HTTPException

class AppConnectionError(HTTPException):
    def __init__(self, message: str = 'something went wrong with connection!', status_code: int = 503) -> None:
        super().__init__(detail=message, status_code=status_code)


class ElasticSearchConnectionError(AppConnectionError):
    def __init__(self, message: str = 'Failed to connect to elastic search', status_code: int = 504) -> None:
        super().__init__(message=message, status_code=status_code)


class ExternalToolConnectionError(AppConnectionError):
    def __init__(self, message: str = 'Failed to connect to external tool', status_code: int = 503) -> None:
        super().__init__(message=message, status_code=status_code)


class ElasticSearchQueryError(HTTPException):
    def __init__(self, message: str = 'Failed to query elasticsearch', status_code: int = 500) -> None:
        super().__init__(detail=message, status_code=status_code)


class DataValidationError(HTTPException):
    def __init__(self, message: str = 'Data validation failed', status_code: int = 422) -> None:
        super().__init__(detail=message, status_code=status_code)


class TJ3ProcessError(HTTPException):
    def __init__(self, message: str = 'TJ3 process failed', status_code: int = 500) -> None:
        super().__init__(detail=message, status_code=status_code)


class BadConfigurationError(HTTPException):
    def __init__(self, message: str = 'Bad configuration', status_code: int = 500) -> None:
        super().__init__(detail=message, status_code=status_code)


class ProcessFailureError(HTTPException):
    def __init__(self, message: str = 'Process failed', status_code: int = 500) -> None:
        super().__init__(detail=message, status_code=status_code)


class BadDataError(HTTPException):
    def __init__(self, message: str = "Bad input!", status_code: int = 400)-> None:
        super().__init__(detail=message, status_code=status_code)
