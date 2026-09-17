class ServiceException(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(message if message else self.__class__.__name__)


# Bonus Exceptions
class BonusAlreadyEnabledError(ServiceException):
    pass


class BonusAlreadyDisabledError(ServiceException):
    pass


class BonusAlreadyRemovedError(ServiceException):
    pass


class BonusAlreadyRequestError(ServiceException):
    pass


class BonusAlreadyNotRequestError(ServiceException):
    pass


class BonusAlreadyAllError(ServiceException):
    pass


class BonusAlreadyNegativeError(ServiceException):
    pass


class BonusAlreadyNeutralError(ServiceException):
    pass


class BonusAlreadyPositiveError(ServiceException):
    pass


class BonusAlreadyVipError(ServiceException):
    pass


class BonusAlreadyApprovedError(ServiceException):
    pass


class BonusAlreadyActivatedError(ServiceException):
    pass


class BonusAlreadyCanceledError(ServiceException):
    pass


# User Exceptions
class UserAlreadyBlockedError(ServiceException):
    pass


class UserAlreadyUnblockedError(ServiceException):
    pass


class UserAlreadyAllError(ServiceException):
    pass


class UserAlreadyNegativeError(ServiceException):
    pass


class UserAlreadyNeutralError(ServiceException):
    pass


class UserAlreadyPositiveError(ServiceException):
    pass


class UserAlreadyVipError(ServiceException):
    pass


# Country Exceptions
class CountryAlreadyEnabledError(ServiceException):
    pass


class CountryAlreadyDisabledError(ServiceException):
    pass


class CountryAlreadyRemovedError(ServiceException):
    pass


class CountryNotFoundError(ServiceException):
    pass
