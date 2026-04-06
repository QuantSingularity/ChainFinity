"""
Portfolio-specific exceptions for ChainFinity
"""

from .base_exceptions import (
    BaseChainFinityException,
    BusinessLogicException,
    ErrorCategory,
    ErrorSeverity,
    InsufficientResourcesException,
    ResourceNotFoundException,
)


class PortfolioNotFoundError(ResourceNotFoundException):
    """Raised when a portfolio cannot be found"""

    def __init__(self, portfolio_id=None, message=None):
        msg = message or f"Portfolio not found: {portfolio_id}"
        super().__init__(message=msg, error_code="PORTFOLIO_NOT_FOUND")


class InsufficientFundsError(InsufficientResourcesException):
    """Raised when there are insufficient funds to complete an operation"""

    def __init__(self, required=None, available=None, message=None):
        if message:
            msg = message
        elif required is not None and available is not None:
            msg = f"Insufficient funds: required {required}, available {available}"
        else:
            msg = "Insufficient funds to complete the operation"
        super().__init__(message=msg, error_code="INSUFFICIENT_FUNDS")


class InvalidAllocationError(BaseChainFinityException):
    """Raised when portfolio allocation percentages are invalid"""

    def __init__(self, message=None):
        msg = message or "Total allocation exceeds 100%"
        super().__init__(
            message=msg,
            error_code="INVALID_ALLOCATION",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
        )


class PortfolioLimitExceededError(BusinessLogicException):
    """Raised when a user has reached their maximum portfolio limit"""

    def __init__(self, limit=None, message=None):
        msg = message or f"Maximum portfolio limit reached ({limit})"
        super().__init__(message=msg, error_code="PORTFOLIO_LIMIT_EXCEEDED")


class AssetNotFoundError(ResourceNotFoundException):
    """Raised when an asset cannot be found in a portfolio"""

    def __init__(self, asset_id=None, message=None):
        msg = message or f"Asset not found: {asset_id}"
        super().__init__(message=msg, error_code="ASSET_NOT_FOUND")


class InvalidPortfolioOperationError(BusinessLogicException):
    """Raised when an invalid operation is attempted on a portfolio"""

    def __init__(self, message=None):
        msg = message or "Invalid portfolio operation"
        super().__init__(message=msg, error_code="INVALID_PORTFOLIO_OPERATION")
