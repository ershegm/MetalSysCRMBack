"""
Dependency Injection для API
"""
from functools import lru_cache
from ..services import AuthService, UserService, ProposalService, AIService, FileService
from ..services.calculation_service import CalculationService
from ..core.security import security_manager


@lru_cache()
def get_auth_service() -> AuthService:
    """Получить сервис аутентификации"""
    return AuthService()


@lru_cache()
def get_user_service() -> UserService:
    """Получить сервис пользователей"""
    return UserService()


@lru_cache()
def get_proposal_service() -> ProposalService:
    """Получить сервис предложений"""
    return ProposalService()


@lru_cache()
def get_ai_service() -> AIService:
    """Получить сервис ИИ"""
    return AIService()


@lru_cache()
def get_file_service() -> FileService:
    """Получить сервис файлов"""
    return FileService()


@lru_cache()
def get_calculation_service() -> CalculationService:
    """Получить сервис расчетов"""
    return CalculationService()



