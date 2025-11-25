import pytest

from backend.app.utils.customer_rules import validate_customer_fields, CUSTOMER_TYPE_RULES


def test_legal_entity_requires_full_requisites():
    payload = {'name': 'ООО Тест'}
    with pytest.raises(ValueError):
        validate_customer_fields(1, payload, allow_partial=False)

    payload.update({'inn': '7701234567', 'kpp': '770101001', 'ogrn': '1234567890123'})
    validate_customer_fields(1, payload, allow_partial=False)


def test_individual_clears_requisites():
    payload = {
        'name': 'Иван Петров',
        'inn': '1234567890',
        'kpp': '123',
        'ogrn': '123',
    }
    validate_customer_fields(3, payload, allow_partial=False)
    assert payload['inn'] == ''
    assert payload['kpp'] == ''
    assert payload['ogrn'] == ''


def test_hidden_fields_for_ip():
    payload = {
        'name': 'ИП Тест',
        'inn': '123456789012',
        'kpp': '999999999',
        'ogrn': '123456789012345',
    }
    validate_customer_fields(2, payload, allow_partial=False)
    assert payload['kpp'] == ''


