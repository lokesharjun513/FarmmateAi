# app/shared/exceptions.py


# ============================================================
# BASE APPLICATION EXCEPTION
# ============================================================


class FarmMateError(Exception):
    """
    Base exception for all expected FarmMate AI application
    and business errors.
    """

    pass


# ============================================================
# AUTHENTICATION / AUTHORIZATION
# ============================================================


class AuthenticationError(FarmMateError):
    """
    Base exception for authentication-related failures.
    """

    pass


class InvalidCredentialsError(AuthenticationError):
    """
    Raised when login credentials are invalid.
    """

    pass


class UnauthorizedError(AuthenticationError):
    """
    Raised when authentication or authorization fails.
    """

    pass


# ============================================================
# USER
# ============================================================


class UserError(FarmMateError):
    """
    Base exception for user-related business errors.
    """

    pass


class EmailAlreadyExistsError(UserError):
    """
    Raised when an email is already registered.
    """

    pass


class MobileAlreadyExistsError(UserError):
    """
    Raised when a mobile number is already registered.
    """

    pass


# ============================================================
# FARMER
# ============================================================


class FarmerError(FarmMateError):
    """
    Base exception for farmer-related business errors.
    """

    pass


class FarmerProfileAlreadyExistsError(FarmerError):
    """
    Raised when a farmer profile already exists.
    """

    pass


class FarmerProfileNotFoundError(FarmerError):
    """
    Raised when a farmer profile cannot be found.
    """

    pass


# ============================================================
# FARM
# ============================================================


class FarmError(FarmMateError):
    """
    Base exception for farm-related business errors.
    """

    pass


class FarmNotFoundError(FarmError):
    """
    Raised when a farm cannot be found.
    """

    pass


class FarmAccessDeniedError(FarmError):
    """
    Raised when a user attempts to access another farmer's
    farm.
    """

    pass


# ============================================================
# CROP SEASON
# ============================================================


class CropSeasonError(FarmMateError):
    """
    Base exception for crop-season-related business errors.
    """

    pass


class CropSeasonNotFoundError(CropSeasonError):
    """
    Raised when a crop season cannot be found.
    """

    pass


# ============================================================
# ACTIVITY
# ============================================================


class ActivityError(FarmMateError):
    """
    Base exception for activity-related business errors.
    """

    pass


class ActivityNotFoundError(ActivityError):
    """
    Raised when an activity cannot be found.
    """

    pass


# ============================================================
# VALIDATION
# ============================================================


class ValidationError(FarmMateError):
    """
    Raised for business validation failures.
    """

    pass


# ============================================================
# DASHBOARD
# ============================================================


class DashboardError(FarmMateError):
    """
    Raised when dashboard processing fails.
    """

    pass


# ============================================================
# EXTERNAL / APPLICATION SERVICES
# ============================================================


class ServiceError(FarmMateError):
    """
    Base exception for application and external service
    failures.
    """

    pass


class WeatherServiceError(ServiceError):
    """
    Raised when weather service processing fails.
    """

    pass


class AIRecommendationError(ServiceError):
    """
    Raised when AI recommendation processing fails.
    """

    pass


# ============================================================
# NOTIFICATION
# ============================================================


class NotificationError(ServiceError):
    """
    Base exception for notification-related failures.
    """

    pass


class NotificationNotFoundError(NotificationError):
    """
    Raised when a notification cannot be found.
    """

    pass