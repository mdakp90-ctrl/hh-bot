#!/usr/bin/env python3
from services.hh_service import CITY_TO_AREA_ID


def test_city_validation():
    # Тестирование поддерживаемых городов
    supported_cities = [
        "Москва",
        "Санкт-Петербург", 
        "Новосибирск",
        "Екатеринбург",
        "Казань",
        "Нижний Новгород",
        "Челябинск",
        "Самара",
        "Омск",
        "Ростов-на-Дону",
        "Уфа",
        "Красноярск",
        "Воронеж",
        "Пермь",
        "Волгоград"
    ]
    
    unsupported_cities = [
        "Токио",
        "Лондон",
        "Нью-Йорк",
        "Минск",
        "Киев"
    ]
    
    print("Проверка поддерживаемых городов:")
    for city in supported_cities:
        is_supported = city in CITY_TO_AREA_ID
        status = "Поддерживается" if is_supported else "Не поддерживается"
        print(f"Город '{city}': {status}")
        if is_supported:
            print(f"  - ID области: {CITY_TO_AREA_ID[city]}")
    
    print("\nПроверка неподдерживаемых городов:")
    for city in unsupported_cities:
        is_supported = city in CITY_TO_AREA_ID
        status = "Поддерживается" if is_supported else "Не поддерживается"
        print(f"Город '{city}': {status}")

if __name__ == "__main__":
    test_city_validation()