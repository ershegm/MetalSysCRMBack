"""
API endpoints для работы со сделками (deals)
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from ...core.security import get_current_user
from ...services.deal_service import DealService
from ...services.file_service import FileService
from ...schemas.deal import (
    DealCreate, DealUpdate, DealResponse, DealListResponse,
    DealProductResponse, DealFileResponse, DealCommentResponse, DealHistoryResponse,
    DealParticipantResponse,
)
from ...schemas.common import PaginatedResponse
from ...utils.enums import FileType


router = APIRouter(prefix="/deals", tags=["Deals"])

deal_service = DealService()
file_service = FileService()


@router.get("", response_model=DealListResponse)
async def get_deals(
    skip: int = 0,
    limit: int = 50,
    funnel_id: Optional[int] = None,
    stage_id: Optional[int] = None,
    company_id: Optional[int] = None,
    responsible_user_id: Optional[int] = None,
    primary_contact_id: Optional[int] = None,
    is_closed: Optional[bool] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
):
    """Получает список сделок с фильтрацией"""
    deals, total = deal_service.get_all(
        skip=skip,
        limit=limit,
        funnel_id=funnel_id,
        stage_id=stage_id,
        company_id=company_id,
        responsible_user_id=responsible_user_id,
        primary_contact_id=primary_contact_id,
        is_closed=is_closed,
        date_from=date_from,
        date_to=date_to,
    )
    
    return DealListResponse(
        data=[DealResponse(**d) for d in deals],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Получает сделку по ID"""
    deal = deal_service.get_by_id(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    return DealResponse(**deal)


@router.post("", response_model=DealResponse, status_code=201)
async def create_deal(
    deal_data: DealCreate,
    current_user: dict = Depends(get_current_user),
):
    """Создаёт новую сделку"""
    deal = deal_service.create(deal_data.dict(), user_id=current_user['id'])
    return DealResponse(**deal)


@router.put("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: int,
    deal_data: DealUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Обновляет сделку"""
    deal = deal_service.update(
        deal_id,
        deal_data.dict(exclude_unset=True),
        user_id=current_user['id'],
    )
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    return DealResponse(**deal)


@router.patch("/{deal_id}/stage", response_model=DealResponse)
async def move_deal_to_stage(
    deal_id: int,
    stage_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """Перемещает сделку на другую стадию"""
    stage_id = stage_data.get('stage_id')
    if not stage_id:
        raise HTTPException(status_code=400, detail="Не указан stage_id")
    
    deal = deal_service.move_to_stage(deal_id, stage_id, current_user['id'])
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    return DealResponse(**deal)


@router.delete("/{deal_id}", status_code=204)
async def delete_deal(
    deal_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Удаляет сделку"""
    success = deal_service.delete(deal_id, current_user['id'])
    if not success:
        raise HTTPException(status_code=404, detail="Сделка не найдена")


@router.post("/{deal_id}/products", response_model=DealProductResponse, status_code=201)
async def add_deal_product(
    deal_id: int,
    product_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """Добавляет товар к сделке"""
    deal = deal_service.get_by_id(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    product = deal_service.add_product(deal_id, product_data, current_user['id'])
    return DealProductResponse(**product)


@router.get("/{deal_id}/products", response_model=list[DealProductResponse])
async def get_deal_products(
    deal_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Получает список товаров сделки"""
    deal = deal_service.get_by_id(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    products = deal_service.get_products(deal_id)
    return [DealProductResponse(**p) for p in products]


@router.delete("/{deal_id}/products/{product_id}", status_code=204)
async def remove_deal_product(
    deal_id: int,
    product_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Удаляет товар из сделки"""
    success = deal_service.remove_product(deal_id, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Сделка или товар не найдены")


@router.post("/{deal_id}/files", response_model=DealFileResponse, status_code=201)
async def upload_deal_file(
    deal_id: int,
    file: UploadFile = File(...),
    file_type: str = Form("OTHER"),
    current_user: dict = Depends(get_current_user),
):
    """Загружает файл/КП к сделке"""
    deal = deal_service.get_by_id(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    try:
        FileType(file_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Некорректный тип файла: {file_type}")
    
    saved_file = file_service.save_upload_file(file, f"deals/{deal_id}")
    deal_file = deal_service.upload_file(
        deal_id=deal_id,
        file_name=saved_file["file_name"],
        file_path=saved_file["file_path"],
        file_type=file_type,
        file_size=saved_file["file_size"],
        mime_type=saved_file["mime_type"],
        user_id=current_user['id'],
    )
    return DealFileResponse(**deal_file)


@router.get("/{deal_id}/files", response_model=list[DealFileResponse])
async def get_deal_files(
    deal_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Получает список файлов сделки"""
    deal = deal_service.get_by_id(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    files = deal_service.get_files(deal_id)
    return [DealFileResponse(**f) for f in files]


@router.delete("/{deal_id}/files/{file_id}", status_code=204)
async def delete_deal_file(
    deal_id: int,
    file_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Удаляет файл сделки"""
    deal_files = deal_service.get_files(deal_id)
    file_record = next((f for f in deal_files if f.get('id') == file_id), None)
    success = deal_service.delete_file(deal_id, file_id)
    if not success:
        raise HTTPException(status_code=404, detail="Сделка или файл не найдены")
    if file_record:
        file_service.delete_file(file_record.get('file_path'))


@router.post("/{deal_id}/comments", response_model=DealCommentResponse, status_code=201)
async def add_deal_comment(
    deal_id: int,
    comment_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """Добавляет комментарий к сделке"""
    deal = deal_service.get_by_id(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    text = comment_data.get('text')
    if not text:
        raise HTTPException(status_code=400, detail="Не указан текст комментария")
    
    comment = deal_service.add_comment(
        deal_id,
        text,
        current_user['id'],
        comment_data.get('parent_comment_id'),
    )
    return DealCommentResponse(**comment)


@router.get("/{deal_id}/comments", response_model=list[DealCommentResponse])
async def get_deal_comments(
    deal_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Получает список комментариев сделки"""
    deal = deal_service.get_by_id(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    comments = deal_service.get_comments(deal_id)
    return [DealCommentResponse(**c) for c in comments]


@router.delete("/{deal_id}/comments/{comment_id}", status_code=204)
async def delete_deal_comment(
    deal_id: int,
    comment_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Удаляет комментарий из сделки"""
    success = deal_service.delete_comment(deal_id, comment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Сделка или комментарий не найдены")


@router.get("/{deal_id}/history", response_model=list[DealHistoryResponse])
async def get_deal_history(
    deal_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Получает историю изменений сделки"""
    deal = deal_service.get_by_id(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    history = deal_service.get_history(deal_id)
    return [DealHistoryResponse(**h) for h in history]


@router.get("/{deal_id}/participants", response_model=list[DealParticipantResponse])
async def get_deal_participants(
    deal_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Возвращает участников сделки"""
    deal = deal_service.get_by_id(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    participants = deal_service.get_participants(deal_id)
    return [DealParticipantResponse(**p) for p in participants]


@router.post("/{deal_id}/participants", response_model=DealParticipantResponse, status_code=201)
async def add_deal_participant(
    deal_id: int,
    participant_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """Добавляет участника к сделке"""
    deal = deal_service.get_by_id(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    try:
        participant = deal_service.add_participant(
            deal_id,
            participant_data.get('contact_id'),
            participant_data.get('user_id'),
            participant_data.get('participant_type', 'PARTICIPANT'),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return DealParticipantResponse(**participant)


@router.delete("/{deal_id}/participants/{participant_id}", status_code=204)
async def remove_deal_participant(
    deal_id: int,
    participant_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Удаляет участника из сделки"""
    success = deal_service.remove_participant(deal_id, participant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Сделка или участник не найдены")

