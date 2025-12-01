#!/usr/bin/env python3
"""
Тестирование отображения вакансий в виде компактных карточек
"""
from handlers.vacancies import format_vacancy

# Тестовые данные вакансии
test_vacancy = {
    "name": "Python-разработчик",
    "employer": {
        "name": "IT Company"
    },
    "area": {
        "name": "Москва"
    },
    "salary": {
        "from": 150000,
        "to": 200000,
        "currency": "RUR"
    },
    "alternate_url": "https://example.com/vacancy/123"
}

def test_vacancy_formatting():
    """Тестируем форматирование вакансии"""
    result = format_vacancy(test_vacancy, 0, 0)
    print("Форматирование вакансии:")
    print(result)
    print("\n" + "="*50 + "\n")
    
    # Проверяем наличие иконок
    assert "💼" in result, "Не найдена иконка должности"
    assert "🏢" in result, "Не найдена иконка компании"
    assert "📍" in result, "Не найдена иконка города"
    assert "💰" in result, "Не найдена иконка зарплаты"
    assert "🔗" in result, "Не найдена иконка ссылки"
    
    print("✅ Все иконки присутствуют в карточке вакансии")
    
    # Тест с разными вариантами зарплаты
    vacancy_no_salary = {
        "name": "Стажер-разработчик",
        "employer": {
            "name": "Маленькая компания"
        },
        "area": {
            "name": "Санкт-Петербург"
        },
        "salary": None,
        "alternate_url": "https://example.com/vacancy/124"
    }
    
    result2 = format_vacancy(vacancy_no_salary, 0, 0)
    print("Вакансия без зарплаты:")
    print(result2)
    
    vacancy_with_min_salary = {
        "name": "Junior Python-разработчик",
        "employer": {
            "name": "Стартап"
        },
        "area": {
            "name": "Новосибирск"
        },
        "salary": {
            "from": 80000,
            "to": None,
            "currency": "RUR"
        },
        "alternate_url": "https://example.com/vacancy/125"
    }
    
    result3 = format_vacancy(vacancy_with_min_salary, 0, 0)
    print("Вакансия с минимальной зарплатой:")
    print(result3)

if __name__ == "__main__":
    test_vacancy_formatting()