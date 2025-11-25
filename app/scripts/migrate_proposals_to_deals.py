"""
Скрипт миграции proposals → deals
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Добавляем корневую директорию проекта в путь
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import db_manager
from app.services.deal_service import DealService
from app.services.funnel_service import FunnelService


def migrate_proposals_to_deals():
    """Мигрирует данные из таблицы proposals в таблицу deals"""
    # Инициализируем таблицы CRM
    db_manager.init_crm_tables()
    
    deal_service = DealService()
    funnel_service = FunnelService()
    
    # Получаем воронку по умолчанию
    default_funnel = funnel_service.get_default()
    if not default_funnel:
        print("Ошибка: Воронка по умолчанию не найдена. Запустите init_default_funnel.py сначала.")
        return False
    
    funnel_id = default_funnel['id']
    
    # Получаем первую стадию воронки (prospect)
    stages = default_funnel.get('stages', [])
    if not stages:
        print("Ошибка: В воронке нет стадий")
        return False
    
    first_stage = stages[0]
    stage_id = first_stage['id']
    
    print(f"Используется воронка: {default_funnel['name']} (ID: {funnel_id})")
    print(f"Используется стадия: {first_stage['name']} (ID: {stage_id})")
    
    # Получаем все предложения
    proposals = db_manager.get_proposals()
    print(f"Найдено предложений: {len(proposals)}")
    
    migrated_count = 0
    skipped_count = 0
    
    for proposal in proposals:
        try:
            user_id = proposal.get('user_id')
            if not user_id:
                print(f"Пропущено предложение ID {proposal['id']}: нет user_id")
                skipped_count += 1
                continue
            
            # Определяем название сделки
            company = proposal.get('company', '').strip()
            product_type = proposal.get('productType', '').strip()
            title = f"{company} - {product_type}" if company and product_type else company or product_type or f"Сделка #{proposal['id']}"
            
            # Парсим result JSON для получения товаров
            result_json = proposal.get('result', '{}')
            try:
                if isinstance(result_json, str):
                    result_data = json.loads(result_json)
                else:
                    result_data = result_json
            except json.JSONDecodeError:
                result_data = {}
            
            # Создаём сделку
            deal_data = {
                'title': title,
                'description': f"Мигрировано из предложения #{proposal['id']}",
                'deal_type': 'SALE',
                'funnel_id': funnel_id,
                'stage_id': stage_id,
                'amount': 0,  # Будет пересчитано из товаров
                'is_manual_amount': False,
                'responsible_user_id': user_id,
                'created_by_id': user_id,
            }
            
            # Определяем стадию на основе status/priority из proposal
            status = proposal.get('status', '').strip().lower()
            if status in ['done', 'completed', 'finished']:
                # Ищем стадию "done"
                done_stage = next((s for s in stages if s.get('stage_id') == 'done'), None)
                if done_stage:
                    deal_data['stage_id'] = done_stage['id']
                    deal_data['is_closed'] = True
            
            deal = deal_service.create(deal_data, user_id=user_id)
            deal_id = deal['id']
            
            # Добавляем товары из result
            if isinstance(result_data, dict):
                products = result_data.get('products', [])
                if not products and 'items' in result_data:
                    products = result_data['items']
                
                for product_item in products:
                    if isinstance(product_item, dict):
                        # Пытаемся извлечь данные о товаре
                        name = product_item.get('name') or product_item.get('title') or product_item.get('product', 'Товар')
                        price = float(product_item.get('price', 0) or product_item.get('cost', 0) or 0)
                        quantity = float(product_item.get('quantity', 1) or product_item.get('qty', 1) or 1)
                        unit = product_item.get('unit', 'шт')
                        discount = float(product_item.get('discount', 0) or product_item.get('discount_percent', 0) or 0)
                        
                        if name and price > 0:
                            product_data = {
                                'name': name,
                                'description': product_item.get('description'),
                                'price': price,
                                'quantity': quantity,
                                'unit': unit,
                                'discount_percent': discount,
                            }
                            deal_service.add_product(deal_id, product_data, user_id=user_id)
            
            migrated_count += 1
            if migrated_count % 10 == 0:
                print(f"Мигрировано: {migrated_count}...")
        
        except Exception as e:
            print(f"Ошибка при миграции предложения ID {proposal.get('id')}: {e}")
            skipped_count += 1
            continue
    
    print(f"\nМиграция завершена:")
    print(f"  Мигрировано: {migrated_count}")
    print(f"  Пропущено: {skipped_count}")
    
    return True


if __name__ == "__main__":
    print("Начало миграции proposals → deals...")
    success = migrate_proposals_to_deals()
    if success:
        print("Миграция успешно завершена!")
        sys.exit(0)
    else:
        print("Миграция завершилась с ошибками!")
        sys.exit(1)




