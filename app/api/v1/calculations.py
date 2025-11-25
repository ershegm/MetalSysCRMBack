"""
API роуты для расчетов
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from ..deps import get_calculation_service
from ...models.calculation import CalculationCreate, CalculationUpdate, CalculationResponse
from ...services.calculation_service import CalculationService
from ...core.exceptions import NotFoundError, create_http_exception

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_calculations(
    calculation_service: CalculationService = Depends(get_calculation_service)
):
    """Получение списка расчетов (краткая информация)"""
    return await calculation_service.get_calculations()


@router.get("/{calculation_id}", response_model=Dict[str, Any])
async def get_calculation(
    calculation_id: int,
    calculation_service: CalculationService = Depends(get_calculation_service)
):
    """Получение полного расчета по ID"""
    try:
        return await calculation_service.get_calculation_by_id(calculation_id)
    except NotFoundError as e:
        raise create_http_exception(e)


@router.post("/", response_model=Dict[str, Any])
async def create_calculation(
    calculation_data: CalculationCreate,
    calculation_service: CalculationService = Depends(get_calculation_service)
):
    """Создание нового расчета"""
    return await calculation_service.create_calculation(calculation_data)


@router.put("/{calculation_id}", response_model=Dict[str, Any])
async def update_calculation(
    calculation_id: int,
    calculation_data: CalculationUpdate,
    calculation_service: CalculationService = Depends(get_calculation_service)
):
    """Обновление расчета"""
    try:
        return await calculation_service.update_calculation(calculation_id, calculation_data)
    except NotFoundError as e:
        raise create_http_exception(e)


@router.delete("/{calculation_id}", response_model=Dict[str, bool])
async def delete_calculation(
    calculation_id: int,
    calculation_service: CalculationService = Depends(get_calculation_service)
):
    """Удаление расчета"""
    try:
        return await calculation_service.delete_calculation(calculation_id)
    except NotFoundError as e:
        raise create_http_exception(e)



