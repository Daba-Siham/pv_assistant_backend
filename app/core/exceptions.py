from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: str,
        code: str = "APP_ERROR",
        details: dict | None = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}

        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "message": message,
                "details": self.details
            }
        )


class NotFoundException(AppException):
    def __init__(
        self,
        message: str = "Ressource introuvable",
        details: dict | None = None
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=message,
            details=details
        )


class BadRequestException(AppException):
    def __init__(
        self,
        message: str = "Requête invalide",
        details: dict | None = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="BAD_REQUEST",
            message=message,
            details=details
        )


class UnauthorizedException(AppException):
    def __init__(
        self,
        message: str = "Authentification requise",
        details: dict | None = None
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=message,
            details=details
        )


class ForbiddenException(AppException):
    def __init__(
        self,
        message: str = "Accès refusé",
        details: dict | None = None
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=message,
            details=details
        )


class DatabaseException(AppException):
    def __init__(
        self,
        message: str = "Erreur base de données",
        details: dict | None = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="DATABASE_ERROR",
            message=message,
            details=details
        )


class ExternalAPIException(AppException):
    def __init__(
        self,
        message: str = "Erreur lors de l'appel à une API externe",
        details: dict | None = None
    ):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="EXTERNAL_API_ERROR",
            message=message,
            details=details
        )


class CalculationException(AppException):
    def __init__(
        self,
        message: str = "Erreur pendant le calcul photovoltaïque",
        details: dict | None = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="CALCULATION_ERROR",
            message=message,
            details=details
        )


class MonitoringException(AppException):
    def __init__(
        self,
        message: str = "Erreur pendant le monitoring",
        details: dict | None = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="MONITORING_ERROR",
            message=message,
            details=details
        )


class LLMException(AppException):
    def __init__(
        self,
        message: str = "Erreur pendant la génération de réponse IA",
        details: dict | None = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="LLM_ERROR",
            message=message,
            details=details
        )