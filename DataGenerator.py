import random

class DataGenerator:

    TASK_NAMES = [
            "Разработка API",
            "Исправление ошибки",
            "Написание документации",
            "Рефакторинг модуля",
            "Добавление логирования",
            "Создание тестов",
            "Оптимизация запроса",
            "Обновление зависимостей",
            "Создание UI",
            "Миграция базы данных"
        ]

    def __init__(self, db):
        self.db = db

    # -----------------------------
    # генерация сотрудников
    # -----------------------------
    def generate_employees(self, count, min_hours, max_hours):

        for i in range(count):

            name = f"Сотрудник_{i+1}"

            hours_per_day = random.randint(min_hours, max_hours)

            self.db.add_employee(name, hours_per_day)
        
        return count

    # -----------------------------
    # генерация задач
    # -----------------------------
    def generate_tasks(self, count, min_hours, max_hours):

        for i in range(count):

            description = random.choice(self.TASK_NAMES) + f" #{i+1}"

            hours = random.randint(min_hours, max_hours)

            self.db.add_task(description, hours)

        return count