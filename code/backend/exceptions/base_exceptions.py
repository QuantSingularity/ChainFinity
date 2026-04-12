"""
Comprehensive Exception Handling System for ChainFinity
Provides structured error handling with detailed error codes and messages
"""

import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    NETWORK = "network"
    SYSTEM = "system"
    SECURITY = "security"
    COMPLIANCE = "compliance"


class BaseChainFinityException(Exception):
    """
    Base exception class for all ChainFinity exceptions
    Provides structured error information and logging capabilities
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.user_message = user_message or message
        self.suggestions = suggestions or []
        self.correlation_id = correlation_id
        self.timestamp = datetime.now(timezone.utc)
        self.traceback = traceback.format_exc()

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "user_message": self.user_message,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
        }

    def to_log_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging"""
        log_dict = self.to_dict()
        log_dict.update(
            {"traceback": self.traceback, "exception_type": self.__class__.__name__}
        )
        return log_dict

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(error_code='{self.error_code}', message='{self.message}', category={self.category}, severity={self.severity})"


class ValidationException(BaseChainFinityException):
    """Exception for validation errors"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        validation_errors: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        if validation_errors:
            details["validation_errors"] = validation_errors
        kwargs.update(
            {
                "category": ErrorCategory.VALIDATION,
                "severity": ErrorSeverity.LOW,
                "details": details,
            }
        )
        super().__init__(message, **kwargs)
        self.field = field
        self.value = value
        self.validation_errors = validation_errors or []


class AuthenticationException(BaseChainFinityException):
    """Exception for authentication errors"""

    def __init__(self, message: str, **kwargs) -> None:
        kwargs.update(
            {
                "category": ErrorCategory.AUTHENTICATION,
                "severity": ErrorSeverity.HIGH,
                "user_message": "Authentication failed. Please check your credentials.",
            }
        )
        super().__init__(message, **kwargs)


class AuthorizationException(BaseChainFinityException):
    """Exception for authorization errors"""

    def __init__(
        self,
        message: str,
        required_permission: Optional[str] = None,
        user_permissions: Optional[List[str]] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
        if required_permission:
            details["required_permission"] = required_permission
        if user_permissions:
            details["user_permissions"] = user_permissions
        kwargs.update(
            {
                "category": ErrorCategory.AUTHORIZATION,
                "severity": ErrorSeverity.HIGH,
                "details": details,
                "user_message": "You don't have permission to perform this action.",
            }
        )
        super().__init__(message, **kwargs)
        self.required_permission = required_permission
        self.user_permissions = user_permissions or []


class BusinessLogicException(BaseChainFinityException):
    """Exception for business logic violations"""

    def __init__(self, message: str, **kwargs) -> None:
        kwargs.update(
            {"category": ErrorCategory.BUSINESS_LOGIC, "severity": ErrorSeverity.MEDIUM}
        )
        super().__init__(message, **kwargs)


class ExternalServiceException(BaseChainFinityException):
    """Exception for external service errors"""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
        if service_name:
            details["service_name"] = service_name
        if status_code:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body
        kwargs.update(
            {
                "category": ErrorCategory.EXTERNAL_SERVICE,
                "severity": ErrorSeverity.MEDIUM,
                "details": details,
                "user_message": "External service is temporarily unavailable. Please try again later.",
            }
        )
        super().__init__(message, **kwargs)
        self.service_name = service_name
        self.status_code = status_code
        self.response_body = response_body


class DatabaseException(BaseChainFinityException):
    """Exception for database errors"""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table
        kwargs.update(
            {
                "category": ErrorCategory.DATABASE,
                "severity": ErrorSeverity.HIGH,
                "details": details,
                "user_message": "Database operation failed. Please try again later.",
            }
        )
        super().__init__(message, **kwargs)
        self.operation = operation
        self.table = table


class NetworkException(BaseChainFinityException):
    """Exception for network-related errors"""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
        if url:
            details["url"] = url
        if timeout:
            details["timeout"] = timeout
        kwargs.update(
            {
                "category": ErrorCategory.NETWORK,
                "severity": ErrorSeverity.MEDIUM,
                "details": details,
                "user_message": "Network error occurred. Please check your connection and try again.",
            }
        )
        super().__init__(message, **kwargs)
        self.url = url
        self.timeout = timeout


class SecurityException(BaseChainFinityException):
    """Exception for security-related errors"""

    def __init__(
        self,
        message: str,
        security_event: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
        if security_event:
            details["security_event"] = security_event
        if ip_address:
            details["ip_address"] = ip_address
        if user_agent:
            details["user_agent"] = user_agent
        kwargs.update(
            {
                "category": ErrorCategory.SECURITY,
                "severity": ErrorSeverity.CRITICAL,
                "details": details,
                "user_message": "Security violation detected. Access denied.",
            }
        )
        super().__init__(message, **kwargs)
        self.security_event = security_event
        self.ip_address = ip_address
        self.user_agent = user_agent


class ComplianceException(BaseChainFinityException):
    """Exception for compliance violations"""

    def __init__(
        self,
        message: str,
        regulation: Optional[str] = None,
        violation_type: Optional[str] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
        if regulation:
            details["regulation"] = regulation
        if violation_type:
            details["violation_type"] = violation_type
        kwargs.update(
            {
                "category": ErrorCategory.COMPLIANCE,
                "severity": ErrorSeverity.HIGH,
                "details": details,
                "user_message": "Compliance violation detected. Operation blocked.",
            }
        )
        super().__init__(message, **kwargs)
        self.regulation = regulation
        self.violation_type = violation_type


class RateLimitException(BaseChainFinityException):
    """Exception for rate limiting"""

    def __init__(
        self,
        message: str,
        limit: Optional[int] = None,
        window: Optional[int] = None,
        retry_after: Optional[int] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
        if limit:
            details["limit"] = limit
        if window:
            details["window"] = window
        if retry_after:
            details["retry_after"] = retry_after
        kwargs.update(
            {
                "category": ErrorCategory.SYSTEM,
                "severity": ErrorSeverity.MEDIUM,
                "details": details,
                "user_message": f"Rate limit exceeded. Please try again in {retry_after or 60} seconds.",
            }
        )
        super().__init__(message, **kwargs)
        self.limit = limit
        self.window = window
        self.retry_after = retry_after


class ConfigurationException(BaseChainFinityException):
    """Exception for configuration errors"""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[str] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key
        if config_value:
            details["config_value"] = config_value
        kwargs.update(
            {
                "category": ErrorCategory.SYSTEM,
                "severity": ErrorSeverity.CRITICAL,
                "details": details,
                "user_message": "System configuration error. Please contact support.",
            }
        )
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.config_value = config_value


class ResourceNotFoundException(BaseChainFinityException):
    """Exception for resource not found errors"""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        kwargs.update(
            {
                "category": ErrorCategory.BUSINESS_LOGIC,
                "severity": ErrorSeverity.LOW,
                "details": details,
                "user_message": f"The requested {resource_type or 'resource'} was not found.",
            }
        )
        super().__init__(message, **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ConflictException(BaseChainFinityException):
    """Exception for resource conflicts"""

    def __init__(
        self, message: str, conflicting_resource: Optional[str] = None, **kwargs
    ) -> None:
        details = kwargs.get("details", {})
        if conflicting_resource:
            details["conflicting_resource"] = conflicting_resource
        kwargs.update(
            {
                "category": ErrorCategory.BUSINESS_LOGIC,
                "severity": ErrorSeverity.MEDIUM,
                "details": details,
                "user_message": "Resource conflict detected. Please resolve and try again.",
            }
        )
        super().__init__(message, **kwargs)
        self.conflicting_resource = conflicting_resource


class InsufficientResourcesException(BaseChainFinityException):
    """Exception for insufficient resources"""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        required_amount: Optional[str] = None,
        available_amount: Optional[str] = None,
        **kwargs,
    ) -> None:
        details = kwargs.get("details", {})
        if resource_type:
            details["resource_type"] = resource_type
        if required_amount:
            details["required_amount"] = required_amount
        if available_amount:
            details["available_amount"] = available_amount
        kwargs.update(
            {
                "category": ErrorCategory.BUSINESS_LOGIC,
                "severity": ErrorSeverity.MEDIUM,
                "details": details,
                "user_message": f"Insufficient {resource_type or 'resources'} available.",
            }
        )
        super().__init__(message, **kwargs)
        self.resource_type = resource_type
        self.required_amount = required_amount
        self.available_amount = available_amount


class ErrorCodes:
    """Centralized error codes for consistent error handling"""

    INVALID_CREDENTIALS = "AUTH_1001"
    TOKEN_EXPIRED = "AUTH_1002"
    TOKEN_INVALID = "AUTH_1003"
    ACCOUNT_LOCKED = "AUTH_1004"
    MFA_REQUIRED = "AUTH_1005"
    MFA_INVALID = "AUTH_1006"
    INSUFFICIENT_PERMISSIONS = "AUTHZ_1101"
    ROLE_NOT_FOUND = "AUTHZ_1102"
    PERMISSION_DENIED = "AUTHZ_1103"
    RESOURCE_ACCESS_DENIED = "AUTHZ_1104"
    INVALID_INPUT = "VAL_1201"
    MISSING_REQUIRED_FIELD = "VAL_1202"
    INVALID_FORMAT = "VAL_1203"
    VALUE_OUT_OF_RANGE = "VAL_1204"
    INVALID_EMAIL = "VAL_1205"
    INVALID_PASSWORD = "VAL_1206"
    PORTFOLIO_NOT_FOUND = "PORT_2001"
    PORTFOLIO_LIMIT_EXCEEDED = "PORT_2002"
    INVALID_ALLOCATION = "PORT_2003"
    INSUFFICIENT_FUNDS = "PORT_2004"
    ASSET_NOT_FOUND = "PORT_2005"
    PORTFOLIO_LOCKED = "PORT_2006"
    RISK_LIMIT_EXCEEDED = "RISK_2101"
    INVALID_RISK_PARAMETERS = "RISK_2102"
    RISK_CALCULATION_FAILED = "RISK_2103"
    STRESS_TEST_FAILED = "RISK_2104"
    MARKET_DATA_UNAVAILABLE = "MKT_2201"
    INVALID_SYMBOL = "MKT_2202"
    PRICE_FEED_ERROR = "MKT_2203"
    HISTORICAL_DATA_MISSING = "MKT_2204"
    EXTERNAL_API_ERROR = "EXT_3001"
    SERVICE_UNAVAILABLE = "EXT_3002"
    TIMEOUT_ERROR = "EXT_3003"
    RATE_LIMIT_EXCEEDED = "EXT_3004"
    DATABASE_CONNECTION_ERROR = "DB_4001"
    QUERY_EXECUTION_ERROR = "DB_4002"
    CONSTRAINT_VIOLATION = "DB_4003"
    TRANSACTION_FAILED = "DB_4004"
    INTERNAL_SERVER_ERROR = "SYS_5001"
    CONFIGURATION_ERROR = "SYS_5002"
    RESOURCE_EXHAUSTED = "SYS_5003"
    SERVICE_DEGRADED = "SYS_5004"
    SECURITY_VIOLATION = "SEC_6001"
    SUSPICIOUS_ACTIVITY = "SEC_6002"
    IP_BLOCKED = "SEC_6003"
    ENCRYPTION_ERROR = "SEC_6004"
    KYC_REQUIRED = "COMP_7001"
    AML_VIOLATION = "COMP_7002"
    REGULATORY_LIMIT_EXCEEDED = "COMP_7003"
    COMPLIANCE_CHECK_FAILED = "COMP_7004"


class ExceptionFactory:
    """Factory for creating exceptions with predefined error codes"""

    @staticmethod
    def create_validation_error(
        message: str, field: Optional[str] = None, value: Optional[Any] = None, **kwargs
    ) -> ValidationException:
        return ValidationException(
            message=message,
            error_code=ErrorCodes.INVALID_INPUT,
            field=field,
            value=value,
            **kwargs,
        )

    @staticmethod
    def create_authentication_error(message: str, **kwargs) -> AuthenticationException:
        return AuthenticationException(
            message=message, error_code=ErrorCodes.INVALID_CREDENTIALS, **kwargs
        )

    @staticmethod
    def create_authorization_error(
        message: str, required_permission: Optional[str] = None, **kwargs
    ) -> AuthorizationException:
        return AuthorizationException(
            message=message,
            error_code=ErrorCodes.INSUFFICIENT_PERMISSIONS,
            required_permission=required_permission,
            **kwargs,
        )

    @staticmethod
    def create_not_found_error(
        resource_type: str, resource_id: Optional[str] = None, **kwargs
    ) -> ResourceNotFoundException:
        message = f"{resource_type} not found"
        if resource_id:
            message += f" with ID: {resource_id}"
        return ResourceNotFoundException(
            message=message,
            error_code=f"{resource_type.upper()}_NOT_FOUND",
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs,
        )

    @staticmethod
    def create_external_service_error(
        service_name: str, status_code: Optional[int] = None, **kwargs
    ) -> ExternalServiceException:
        message = f"External service error: {service_name}"
        if status_code:
            message += f" (HTTP {status_code})"
        return ExternalServiceException(
            message=message,
            error_code=ErrorCodes.EXTERNAL_API_ERROR,
            service_name=service_name,
            status_code=status_code,
            **kwargs,
        )

    @staticmethod
    def create_database_error(
        operation: str, table: Optional[str] = None, **kwargs
    ) -> DatabaseException:
        message = f"Database error during {operation}"
        if table:
            message += f" on table {table}"
        return DatabaseException(
            message=message,
            error_code=ErrorCodes.QUERY_EXECUTION_ERROR,
            operation=operation,
            table=table,
            **kwargs,
        )


def handle_exception(
    exception: Exception,
    correlation_id: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None,
) -> BaseChainFinityException:
    """
    Convert any exception to a ChainFinity exception with proper context
    """
    if isinstance(exception, BaseChainFinityException):
        if correlation_id and (not exception.correlation_id):
            exception.correlation_id = correlation_id
        if additional_context:
            exception.details.update(additional_context)
        return exception
    if isinstance(exception, ValueError):
        return ValidationException(
            message=str(exception),
            error_code=ErrorCodes.INVALID_INPUT,
            correlation_id=correlation_id,
            details=additional_context or {},
        )
    elif isinstance(exception, PermissionError):
        return AuthorizationException(
            message=str(exception),
            error_code=ErrorCodes.PERMISSION_DENIED,
            correlation_id=correlation_id,
            details=additional_context or {},
        )
    elif isinstance(exception, ConnectionError):
        return NetworkException(
            message=str(exception),
            error_code=ErrorCodes.SERVICE_UNAVAILABLE,
            correlation_id=correlation_id,
            details=additional_context or {},
        )
    else:
        return BaseChainFinityException(
            message=str(exception),
            error_code=ErrorCodes.INTERNAL_SERVER_ERROR,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            correlation_id=correlation_id,
            details=additional_context or {},
        )


def create_error_response(
    exception: BaseChainFinityException, include_traceback: bool = False
) -> Dict[str, Any]:
    """
    Create a standardized error response for API endpoints
    """
    response = {"success": False, "error": exception.to_dict()}
    if include_traceback and exception.traceback:
        response["error"]["traceback"] = exception.traceback
    return response
