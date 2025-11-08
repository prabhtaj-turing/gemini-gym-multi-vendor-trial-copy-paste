class OrderNotFoundError(Exception):
    pass


class NonPendingOrderError(Exception):
    pass


class InvalidCancelReasonError(Exception):
    pass


class NonDeliveredOrderError(Exception):
    pass


class ItemNotFoundError(Exception):
    pass


class ItemMismatchError(Exception):
    pass


class ItemNotAvailableError(Exception):
    pass


class PaymentMethodNotFoundError(Exception):
    pass


class InsufficientGiftCardBalanceError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class InvalidInputError(ValueError):
    pass


class ProductNotFoundError(Exception):
    pass


class InvalidPaymentInfoError(Exception):
    pass


class SamePaymentMethodError(Exception):
    pass


class InvalidReturnPaymentMethodError(Exception):
    pass


class InvalidExpressionError(Exception):
    pass


class DataConflictError(Exception):
    pass
