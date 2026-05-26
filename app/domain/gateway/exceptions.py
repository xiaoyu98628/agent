from app.domain.exceptions import DomainError


class GatewayError(DomainError):
    """Gateway 通用错误。"""


class UnauthorizedGatewayChatError(GatewayError):
    """chat id 不在白名单。"""
