from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class BaseAppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}


class AuthenticationException(BaseAppException):
    def __init__(self, message: str = "Could not authenticate credentials", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, detail)


class ForbiddenException(BaseAppException):
    def __init__(self, message: str = "Operation not permitted", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_403_FORBIDDEN, detail)


class NotFoundException(BaseAppException):
    def __init__(self, message: str = "Requested resource not found", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_404_NOT_FOUND, detail)


class ValidationException(BaseAppException):
    def __init__(self, message: str = "Invalid input values", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, detail)


class ToolException(BaseAppException):
    def __init__(self, message: str = "Agent tool execution failed", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, detail)


class LLMException(BaseAppException):
    def __init__(self, message: str = "LLM generation failed", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_502_BAD_GATEWAY, detail)


class ExternalServiceException(BaseAppException):
    def __init__(self, message: str = "External service integration failed", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_502_BAD_GATEWAY, detail)
