"""
API endpoints для работы с контактами (contacts)
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from ...core.security import get_current_user
from ...services.contact_service import ContactService
from ...schemas.contact import ContactCreate, ContactUpdate, ContactResponse, ContactListResponse
from ...schemas.common import PaginatedResponse


router = APIRouter(prefix="/contacts", tags=["Contacts"])

contact_service = ContactService()


@router.get("", response_model=ContactListResponse)
async def get_contacts(
    skip: int = 0,
    limit: int = 50,
    company_id: Optional[int] = None,
    responsible_user_id: Optional[int] = None,
    tags: Optional[List[str]] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
):
    """Получает список контактов с фильтрацией"""
    contacts, total = contact_service.get_all(
        skip=skip,
        limit=limit,
        company_id=company_id,
        responsible_user_id=responsible_user_id,
        tags=tags,
        search=search,
        is_active=is_active,
    )
    
    return ContactListResponse(
        data=[ContactResponse(**c) for c in contacts],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Получает контакт по ID"""
    contact = contact_service.get_by_id(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Контакт не найден")
    
    return ContactResponse(**contact)


@router.post("", response_model=ContactResponse, status_code=201)
async def create_contact(
    contact_data: ContactCreate,
    current_user: dict = Depends(get_current_user),
):
    """Создаёт новый контакт"""
    contact = contact_service.create(contact_data.dict(), user_id=current_user['id'])
    return ContactResponse(**contact)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact_data: ContactUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Обновляет контакт"""
    contact = contact_service.update(
        contact_id,
        contact_data.dict(exclude_unset=True),
        user_id=current_user['id'],
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Контакт не найден")
    return ContactResponse(**contact)


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Удаляет контакт"""
    success = contact_service.delete(contact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Контакт не найден")


@router.post("/{contact_id}/communications", response_model=ContactResponse)
async def add_communication(
    contact_id: int,
    communication: dict,
    current_user: dict = Depends(get_current_user),
):
    """Добавляет коммуникацию к контакту"""
    contact = contact_service.add_communication(contact_id, communication)
    if not contact:
        raise HTTPException(status_code=404, detail="Контакт не найден")
    return ContactResponse(**contact)


@router.delete("/{contact_id}/communications/{comm_id}", status_code=204)
async def remove_communication(
    contact_id: int,
    comm_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Удаляет коммуникацию из контакта"""
    contact = contact_service.remove_communication(contact_id, comm_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Контакт не найден или коммуникация не найдена")


@router.post("/{contact_id}/tags", response_model=ContactResponse)
async def add_tag(
    contact_id: int,
    tag_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """Добавляет тег к контакту"""
    tag_name = tag_data.get('tag_name') or tag_data.get('name')
    if not tag_name:
        raise HTTPException(status_code=400, detail="Не указано имя тега")
    
    contact = contact_service.add_tag(contact_id, tag_name)
    if not contact:
        raise HTTPException(status_code=404, detail="Контакт не найден")
    return ContactResponse(**contact)


@router.delete("/{contact_id}/tags/{tag_name}", status_code=204)
async def remove_tag(
    contact_id: int,
    tag_name: str,
    current_user: dict = Depends(get_current_user),
):
    """Удаляет тег из контакта"""
    contact = contact_service.remove_tag(contact_id, tag_name)
    if not contact:
        raise HTTPException(status_code=404, detail="Контакт не найден")

