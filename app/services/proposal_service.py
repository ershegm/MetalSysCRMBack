"""
Сервис предложений
"""
from typing import List, Dict, Any, Optional
from ..core.database import db_manager
from ..core.exceptions import NotFoundError
from ..models.proposal import ProposalCreate, ProposalUpdate


class ProposalService:
    """Сервис управления предложениями"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    async def get_proposals(self, user_id: int = 1) -> List[Dict[str, Any]]:
        """Получение всех предложений пользователя"""
        return self.db_manager.get_proposals(user_id)
    
    async def get_proposal_by_id(self, proposal_id: int) -> Optional[Dict[str, Any]]:
        """Получение предложения по ID"""
        return self.db_manager.get_proposal_by_id(proposal_id)
    
    async def create_proposal(self, proposal_data: ProposalCreate, user_id: int = 1) -> Dict[str, Any]:
        """Создание нового предложения"""
        self.db_manager.add_missing_columns()
        
        proposal_id = self.db_manager.save_proposal({
            'user_id': user_id,
            'company': proposal_data.company,
            'productType': proposal_data.product_type,
            'material': proposal_data.material,
            'materialGrade': proposal_data.material_grade,
            'dimensions': proposal_data.dimensions,
            'selectedOperations': proposal_data.selected_operations,
            'result': proposal_data.result,
            'status': proposal_data.status,
            'priority': proposal_data.priority
        })
        
        return {"message": "Сохранено в историю", "id": proposal_id}
    
    async def update_proposal(self, proposal_id: int, proposal_data: ProposalUpdate) -> Dict[str, Any]:
        """Обновление предложения"""
        # Убедимся, что структура таблицы актуальна, чтобы апдейты не падали молча
        self.db_manager.add_missing_columns()
        # Создаем словарь только с переданными полями
        update_data = {}
        
        if proposal_data.company is not None:
            update_data['company'] = proposal_data.company
        if proposal_data.product_type is not None:
            update_data['productType'] = proposal_data.product_type
        if proposal_data.material is not None:
            update_data['material'] = proposal_data.material
        if proposal_data.material_grade is not None:
            update_data['materialGrade'] = proposal_data.material_grade
        if proposal_data.dimensions is not None:
            update_data['dimensions'] = proposal_data.dimensions
        if proposal_data.selected_operations is not None:
            update_data['selectedOperations'] = proposal_data.selected_operations
        if proposal_data.result is not None:
            update_data['result'] = proposal_data.result
        if proposal_data.status is not None:
            update_data['status'] = proposal_data.status
        if proposal_data.priority is not None:
            update_data['priority'] = proposal_data.priority
            
        updated_proposal = self.db_manager.update_proposal(proposal_id, update_data)
        
        if not updated_proposal:
            raise NotFoundError("КП не найдено")
        
        return updated_proposal
    
    async def delete_proposal(self, proposal_id: int) -> Dict[str, bool]:
        """Удаление предложения"""
        success = self.db_manager.delete_proposal(proposal_id)
        return {"success": success}


