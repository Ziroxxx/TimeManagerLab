from ScheduleManager import ScheduleManager
from db import Database
from DataGenerator import DataGenerator
from colorama import init, Fore, Style
from PerformanceTester import PerformanceTester
from EventEngine import EventEngine
from ExecuteSimulator import ExecuteSimulator
from TaskJournal import TaskJournal

init(autoreset=True)
db = Database("schedule.db")
generator = DataGenerator(db)

def distribute_tasks():
    manager = ScheduleManager(db)
    return manager.get_printed_schedule()


def distribute_tasks_test():
    try:

        num_runs = int(input(Fore.CYAN + "Сколько прогонов теста выполнить? " + Style.RESET_ALL)) 
        num_tasks = int(input(Fore.CYAN + "Сколько задач генерировать? " + Style.RESET_ALL)) 
        task_hours_min = int(input(Fore.CYAN + "Минимальная трудоемкость задачи (чч): " + Style.RESET_ALL)) 
        task_hours_max = int(input(Fore.CYAN + "Максимальная трудоемкость задачи (чч): " + Style.RESET_ALL)) 
        num_employees = int(input(Fore.CYAN + "Сколько сотрудников? " + Style.RESET_ALL)) 
        emp_hours_min = int(input(Fore.CYAN + "Минимальное число часов в день для сотрудника: " + Style.RESET_ALL)) 
        emp_hours_max = int(input(Fore.CYAN + "Максимальное число часов в день для сотрудника: " + Style.RESET_ALL))

        tester = PerformanceTester(
            db,
            DataGenerator(db),
            ScheduleManager
        )

        avg_time = tester.run_test(
            num_runs,
            num_tasks,
            task_hours_min,
            task_hours_max,
            num_employees,
            emp_hours_min,
            emp_hours_max
        )

        return f"{Fore.GREEN}Тестирование завершено: {num_runs} прогонов, среднее время {avg_time:.4f} сек. Результаты сохранены в performance_results.csv{Style.RESET_ALL}"
    except Exception as e:
        return f"Ошибка: {e}"
    
def simulate_execution():
    try:

        days = int(input("Сколько дней симулировать? "))

        if days <= 0:
            print("Число дней должно быть больше 0")
            return

        event_engine = EventEngine()

        journal = TaskJournal()

        simulator = ExecuteSimulator(
            db,
            event_engine,
            journal
        )

        result = simulator.simulate(days)

        return result + "\nСимуляция успешно завершена"

    except ValueError:
        return "Ошибка: введите корректное число дней"

    # except Exception as e:
    #     return f"Ошибка симуляции: {e}"

def generate_tasks():
    count = int(input(Fore.CYAN + "Количество задач: " + Style.RESET_ALL))
    min_hours = int(input(Fore.CYAN + "Минимальная трудоемкость (чч): " + Style.RESET_ALL))
    max_hours = int(input(Fore.CYAN + "Максимальная трудоемкость (чч): " + Style.RESET_ALL))
    return generator.generate_tasks(count, min_hours, max_hours)


def generate_employees():
    count = int(input(Fore.CYAN + "Количество сотрудников: " + Style.RESET_ALL))
    min_hours = int(input(Fore.CYAN + "Минимальная трудоемкость (чч): " + Style.RESET_ALL))
    max_hours = int(input(Fore.CYAN + "Максимальная трудоемкость (чч): " + Style.RESET_ALL))
    return generator.generate_employees(count, min_hours, max_hours)


def clear_db():
    db.clear_db()


def add_task():
    desc = input(Fore.CYAN + "Описание задачи: " + Style.RESET_ALL)
    hours = int(input(Fore.CYAN + "Трудоемкость (чч): " + Style.RESET_ALL))

    db.add_task(desc, hours)


def add_employee():
    name = input(Fore.CYAN + "ФИО сотрудника: " + Style.RESET_ALL)
    hours_per_day = int(input(Fore.CYAN + "Часов в день: " + Style.RESET_ALL))

    if hours_per_day <= 0:
        print(Fore.RED + "Часов в день должно быть больше 0" + Style.RESET_ALL)
        return

    if hours_per_day > 24:
        print(Fore.RED + "Часов в день должно быть не больше 24" + Style.RESET_ALL)
        return

    db.add_employee(name, hours_per_day)


def delete_task():
    task_id = int(input(Fore.CYAN + "ID Задачи: " + Style.RESET_ALL))
    db.delete_task(task_id)

def delete_employee():
    employee_id = int(input(Fore.CYAN + "ID Сотрудника: " + Style.RESET_ALL))
    db.delete_employee(employee_id)

def get_employees():
    employees = db.get_employees() or []
    if not employees:
        return Fore.RED + "Сотрудников нет." + Style.RESET_ALL
    lines = [Fore.GREEN + "Список сотрудников:\n" + Style.RESET_ALL] + [f"ID: {emp[0]}, ФИО: {emp[1]}, Часов в день: {emp[2]}" for emp in employees]
    return "\n".join(lines)

def get_tasks():
    tasks = db.get_all_tasks() or []
    if not tasks:
        return Fore.RED + "Задач нет." + Style.RESET_ALL
    lines = [Fore.GREEN + "Список задач:\n" + Style.RESET_ALL]
    for task in tasks:
        if task[3] == "NEW":
            status_color = Fore.CYAN
            status_text = "НОВАЯ"
        
        elif task[3] == "SCHEDULED":
            status_color = Fore.YELLOW
            status_text = "ЗАПЛАНИРОВАНА"

        elif task[3] == "IN_PROGRESS":
            status_color = Fore.YELLOW
            status_text = "В РАБОТЕ"

        elif task[3] == "COMPLETED":
            status_color = Fore.GREEN
            status_text = "ВЫПОЛНЕНА"

        lines.append(f"ID: {task[0]}, Описание: {task[1]}, Трудоемкость: {task[2]}, Статус: {status_color}{status_text}{Style.RESET_ALL}")
    return "\n".join(lines)

def get_schedule():
    message = ""
    manager = ScheduleManager(db)
    schedule_str = manager.get_schedule_string()
    if schedule_str:
        message = schedule_str
    else:
        message = Fore.RED + "Расписание пустое" + Style.RESET_ALL
    return message
