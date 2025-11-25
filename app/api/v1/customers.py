"""
API endpoints для работы с клиентами (customers)
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from ...core.security import get_current_user
from ...services.customer_service import CustomerService
from ...services.file_service import FileService
from ...schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
    CustomerFileSchema,
    CustomerMetaResponse,
)
from ...schemas.common import PaginatedResponse
from ...core.database import db_manager
from ...utils.enums import FileType
from ...utils.customer_rules import get_customer_type_meta


router = APIRouter(prefix="/customers", tags=["Customers"])

customer_service = CustomerService()
file_service = FileService()


@router.get("", response_model=CustomerListResponse)
async def get_customers(
    skip: int = 0,
    limit: int = 50,
    customer_type: Optional[int] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
):
    """Получает список клиентов с фильтрацией"""
    customers, total = customer_service.get_all(
        skip=skip,
        limit=limit,
        customer_type=customer_type,
        search=search,
        is_active=is_active,
    )
    
    return CustomerListResponse(
        data=[CustomerResponse(**c) for c in customers],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/meta", response_model=CustomerMetaResponse)
async def get_customer_meta():
    """Возвращает правила отображения и валидации для типов клиентов"""
    return CustomerMetaResponse(types=get_customer_type_meta())


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Получает клиента по ID"""
    customer = customer_service.get_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    return CustomerResponse(**customer)


@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(
    customer_data: CustomerCreate,
    current_user: dict = Depends(get_current_user),
):
    """Создаёт нового клиента"""
    try:
        customer = customer_service.create(customer_data.dict(), user_id=current_user['id'])
        return CustomerResponse(**customer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Обновляет клиента"""
    try:
        customer = customer_service.update(
            customer_id,
            customer_data.dict(exclude_unset=True),
            user_id=current_user['id'],
        )
        if not customer:
            raise HTTPException(status_code=404, detail="Клиент не найден")
        return CustomerResponse(**customer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: int,
    soft: bool = True,
    current_user: dict = Depends(get_current_user),
):
    """Удаляет клиента (soft delete по умолчанию)"""
    success = customer_service.delete(customer_id, soft=soft)
    if not success:
        raise HTTPException(status_code=404, detail="Клиент не найден")


@router.post("/{customer_id}/files", response_model=CustomerFileSchema, status_code=201)
async def upload_customer_file(
    customer_id: int,
    file: UploadFile = File(...),
    file_type: str = Form("OTHER"),
    current_user: dict = Depends(get_current_user),
):
    """Загружает файл для клиента"""
    customer = customer_service.get_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    try:
        FileType(file_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Некорректный тип файла: {file_type}")
    
    saved = file_service.save_upload_file(file, f"customers/{customer_id}")
    customer_file = customer_service.add_file(
        customer_id,
        saved["file_name"],
        saved["file_path"],
        file_type,
        saved["file_size"],
        saved["mime_type"],
        current_user.get('id'),
    )
    if not customer_file:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return CustomerFileSchema(**customer_file)


@router.get("/{customer_id}/files", response_model=list[CustomerFileSchema])
async def get_customer_files(
    customer_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Получает список файлов клиента"""
    customer = customer_service.get_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    return [CustomerFileSchema(**f) for f in customer.get('files', [])]


@router.delete("/{customer_id}/files/{file_id}", status_code=204)
async def delete_customer_file(
    customer_id: int,
    file_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Удаляет файл клиента"""
    customer = customer_service.get_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    file_record = customer_service.delete_file(customer_id, file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="Файл не найден")
    file_service.delete_file(file_record.get('file_path'))

