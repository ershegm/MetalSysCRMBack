"""
API endpoints для работы с воронками (funnels)
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ...core.security import get_current_user
from ...services.funnel_service import FunnelService
from ...schemas.funnel import (
    FunnelCreate, FunnelUpdate, FunnelResponse,
    StageCreate, StageUpdate, StageReorderRequest,
)


router = APIRouter(prefix="/funnels", tags=["Funnels"])

funnel_service = FunnelService()


@router.get("", response_model=List[FunnelResponse])
async def get_funnels(
    current_user: dict = Depends(get_current_user),
):
    """Получает список всех воронок"""
    funnels = funnel_service.get_all()
    return [FunnelResponse(**f) for f in funnels]


@router.get("/default", response_model=FunnelResponse)
async def get_default_funnel(
    current_user: dict = Depends(get_current_user),
):
    """Получает воронку по умолчанию"""
    funnel = funnel_service.get_default()
    if not funnel:
        raise HTTPException(status_code=404, detail="Воронка по умолчанию не найдена")
    return FunnelResponse(**funnel)


@router.get("/{funnel_id}", response_model=FunnelResponse)
async def get_funnel(
    funnel_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Получает воронку по ID"""
    funnel = funnel_service.get_by_id(funnel_id)
    if not funnel:
        raise HTTPException(status_code=404, detail="Воронка не найдена")
    return FunnelResponse(**funnel)


@router.post("", response_model=FunnelResponse, status_code=201)
async def create_funnel(
    funnel_data: FunnelCreate,
    current_user: dict = Depends(get_current_user),
):
    """Создаёт новую воронку"""
    funnel = funnel_service.create(funnel_data.dict(), user_id=current_user['id'])
    return FunnelResponse(**funnel)


@router.put("/{funnel_id}", response_model=FunnelResponse)
async def update_funnel(
    funnel_id: int,
    funnel_data: FunnelUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Обновляет воронку"""
    funnel = funnel_service.update(funnel_id, funnel_data.dict(exclude_unset=True))
    if not funnel:
        raise HTTPException(status_code=404, detail="Воронка не найдена")
    return FunnelResponse(**funnel)


@router.delete("/{funnel_id}", status_code=204)
async def delete_funnel(
    funnel_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Удаляет воронку (нельзя удалить default)"""
    try:
        success = funnel_service.delete(funnel_id)
        if not success:
            raise HTTPException(status_code=404, detail="Воронка не найдена")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{funnel_id}/stages", response_model=dict, status_code=201)
async def add_stage(
    funnel_id: int,
    stage_data: StageCreate,
    current_user: dict = Depends(get_current_user),
):
    """Добавляет стадию к воронке"""
    funnel = funnel_service.get_by_id(funnel_id)
    if not funnel:
        raise HTTPException(status_code=404, detail="Воронка не найдена")
    
    stage = funnel_service.add_stage(funnel_id, stage_data.dict())
    return stage


@router.put("/{funnel_id}/stages/{stage_id}", response_model=dict)
async def update_stage(
    funnel_id: int,
    stage_id: int,
    stage_data: StageUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Обновляет стадию"""
    stage = funnel_service.update_stage(funnel_id, stage_id, stage_data.dict(exclude_unset=True))
    if not stage:
        raise HTTPException(status_code=404, detail="Стадия не найдена")
    return stage


@router.delete("/{funnel_id}/stages/{stage_id}", status_code=204)
async def delete_stage(
    funnel_id: int,
    stage_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Удаляет стадию (перемещает сделки в первую стадию)"""
    success = funnel_service.delete_stage(funnel_id, stage_id)
    if not success:
        raise HTTPException(status_code=404, detail="Воронка или стадия не найдены")


@router.post("/{funnel_id}/set-default", response_model=FunnelResponse)
async def set_default_funnel(
    funnel_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Устанавливает воронку как стандартную"""
    funnel = funnel_service.set_default(funnel_id)
    if not funnel:
        raise HTTPException(status_code=404, detail="Воронка не найдена")
    return FunnelResponse(**funnel)


@router.post("/{funnel_id}/stages/reorder", status_code=200)
async def reorder_stages(
    funnel_id: int,
    reorder_data: StageReorderRequest,
    current_user: dict = Depends(get_current_user),
):
    """Изменяет порядок стадий в воронке"""
    funnel = funnel_service.get_by_id(funnel_id)
    if not funnel:
        raise HTTPException(status_code=404, detail="Воронка не найдена")
    
    success = funnel_service.reorder_stages(funnel_id, reorder_data.stage_ids)
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка изменения порядка стадий")
    
    return {"success": True}

