"""
Валидаторы для CRM системы
"""
import re
from typing import Optional


def validate_inn(inn: str) -> bool:
    """
    Валидация ИНН (10 или 12 цифр с контрольной суммой)
    
    Args:
        inn: ИНН для проверки
        
    Returns:
        True если ИНН валиден, False иначе
    """
    if not inn or not isinstance(inn, str):
        return False
    
    # Убираем пробелы и проверяем что все символы - цифры
    inn_clean = inn.strip().replace(' ', '').replace('-', '')
    if not inn_clean.isdigit():
        return False
    
    length = len(inn_clean)
    
    # ИНН может быть 10 или 12 цифр
    if length not in (10, 12):
        return False
    
    # Проверка контрольной суммы для 10-значного ИНН
    if length == 10:
        coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        check_sum = sum(int(inn_clean[i]) * coefficients[i] for i in range(9)) % 11
        if check_sum > 9:
            check_sum = check_sum % 10
        return check_sum == int(inn_clean[9])
    
    # Проверка контрольной суммы для 12-значного ИНН
    if length == 12:
        # Первая контрольная сумма
        coefficients1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        check_sum1 = sum(int(inn_clean[i]) * coefficients1[i] for i in range(10)) % 11
        if check_sum1 > 9:
            check_sum1 = check_sum1 % 10
        if check_sum1 != int(inn_clean[10]):
            return False
        
        # Вторая контрольная сумма
        coefficients2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        check_sum2 = sum(int(inn_clean[i]) * coefficients2[i] for i in range(11)) % 11
        if check_sum2 > 9:
            check_sum2 = check_sum2 % 10
        return check_sum2 == int(inn_clean[11])
    
    return False


def validate_kpp(kpp: str) -> bool:
    """
    Валидация КПП (9 цифр)
    
    Args:
        kpp: КПП для проверки
        
    Returns:
        True если КПП валиден, False иначе
    """
    if not kpp or not isinstance(kpp, str):
        return False
    
    # Убираем пробелы и проверяем что все символы - цифры
    kpp_clean = kpp.strip().replace(' ', '').replace('-', '')
    if not kpp_clean.isdigit():
        return False
    
    # КПП должен быть 9 цифр
    return len(kpp_clean) == 9


def validate_ogrn(ogrn: str) -> bool:
    """
    Валидация ОГРН (13 или 15 цифр с контрольной суммой)
    
    Args:
        ogrn: ОГРН для проверки
        
    Returns:
        True если ОГРН валиден, False иначе
    """
    if not ogrn or not isinstance(ogrn, str):
        return False
    
    # Убираем пробелы и проверяем что все символы - цифры
    ogrn_clean = ogrn.strip().replace(' ', '').replace('-', '')
    if not ogrn_clean.isdigit():
        return False
    
    length = len(ogrn_clean)
    
    # ОГРН может быть 13 или 15 цифр
    if length not in (13, 15):
        return False
    
    # Проверка контрольной суммы для ОГРН
    if length == 13:
        # Для юридических лиц: проверка остатка от деления на 11
        check_digit = int(ogrn_clean[:-1]) % 11
        if check_digit > 9:
            check_digit = check_digit % 10
        return check_digit == int(ogrn_clean[12])
    else:
        # Для ИП: проверка остатка от деления на 13
        check_digit = int(ogrn_clean[:-1]) % 13
        if check_digit > 9:
            check_digit = check_digit % 10
        return check_digit == int(ogrn_clean[14])
    
    return False


def validate_phone(phone: str) -> bool:
    """
    Валидация телефона (базовая проверка формата)
    
    Args:
        phone: Телефон для проверки
        
    Returns:
        True если телефон валиден, False иначе
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Убираем пробелы, скобки, дефисы
    phone_clean = re.sub(r'[\s\(\)\-]', '', phone.strip())
    
    # Минимальная длина 10 цифр (для российских номеров)
    if len(phone_clean) < 10:
        return False
    
    # Проверяем что это цифры (может начинаться с +)
    if phone_clean.startswith('+'):
        phone_clean = phone_clean[1:]
    
    # Должны быть только цифры
    return phone_clean.isdigit() and len(phone_clean) >= 10


def validate_email(email: str) -> bool:
    """
    Валидация email адреса
    
    Args:
        email: Email для проверки
        
    Returns:
        True если email валиден, False иначе
    """
    if not email or not isinstance(email, str):
        return False
    
    email = email.strip()
    
    # Простая проверка формата email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))





