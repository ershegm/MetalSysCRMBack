"""
API роуты для предложений
"""
from fastapi import APIRouter, Depends
from typing import List
from ..deps import get_proposal_service
from ...models.proposal import ProposalCreate, ProposalUpdate, ProposalResponse
from ...services.proposal_service import ProposalService

router = APIRouter()


@router.get("/", response_model=List[ProposalResponse])
async def get_proposals(
    proposal_service: ProposalService = Depends(get_proposal_service)
):
    """Получение всех предложений"""
    return await proposal_service.get_proposals()


@router.post("/", response_model=dict)
async def create_proposal(
    proposal_data: ProposalCreate,
    proposal_service: ProposalService = Depends(get_proposal_service)
):
    """Создание нового предложения"""
    return await proposal_service.create_proposal(proposal_data)


@router.put("/{proposal_id}", response_model=ProposalResponse)
async def update_proposal(
    proposal_id: int,
    proposal_data: ProposalUpdate,
    proposal_service: ProposalService = Depends(get_proposal_service)
):
    """Обновление предложения"""
    return await proposal_service.update_proposal(proposal_id, proposal_data)


@router.delete("/{proposal_id}")
async def delete_proposal(
    proposal_id: int,
    proposal_service: ProposalService = Depends(get_proposal_service)
):
    """Удаление предложения"""
    return await proposal_service.delete_proposal(proposal_id)
