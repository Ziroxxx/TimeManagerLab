from controllers import *
import os
import platform

last_message = ""

def clear_console():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

def main_menu():
    global last_message
    while True:
        clear_console()

        print("\n--- ГЛАВНОЕ МЕНЮ ---")
        print("1 - Генерация данных")
        print("2 - Работа с БД")
        print("3 - Распределить задачи")
        print("4 - Распределить задачи (тест)")
        print("5 - Симулировать выполнение расписания")
        print("6 - Отчеты")
        print("0 - Выход")

        choice = input("Выбор действия: ")

        if choice == "1":
            generation_menu()

        elif choice == "2":
            db_menu()

        elif choice == "3":
            print(Fore.YELLOW + "Распределение задач...\n" + Style.RESET_ALL)
            last_message = distribute_tasks()

        elif choice == "4":
            print(Fore.YELLOW + "Распределение задач...(тестирование)\n" + Style.RESET_ALL)
            last_message = distribute_tasks_test()

        elif choice == "5":
            print(Fore.YELLOW + "Симуляция выполнения задач...\n" + Style.RESET_ALL)
            last_message = simulate_execution()

        elif choice == "6":
            report_menu()

        elif choice == "0":
            print(Fore.YELLOW + "Выход..." + Style.RESET_ALL)
            break

        else:
            print("Неверный ввод")

        if choice != "0" and last_message != "":
            print(f"\n{last_message}\n")
            input("\nНажмите Enter для продолжения...")
            last_message = ""


# -----------------------
# МЕНЮ ГЕНЕРАЦИИ
# -----------------------

def generation_menu():
    global last_message
    while True:
        clear_console()

        print("\n--- ГЕНЕРАЦИЯ ДАННЫХ ---")
        print("1 - Сгенерировать задачи")
        print("2 - Сгенерировать сотрудников")
        print("0 - Назад")

        choice = input("Выбор: ")

        if choice == "1":
            count = generate_tasks()
            print(Fore.YELLOW + "Генерация задач..." + Style.RESET_ALL)
            last_message = f"{Fore.GREEN}{count} задач сгенерировано{Style.RESET_ALL}"
            

        elif choice == "2":
            count = generate_employees()
            print(Fore.YELLOW + "Генерация сотрудников..." + Style.RESET_ALL)
            last_message = f"{Fore.GREEN}{count} сотрудников сгенерировано{Style.RESET_ALL}"

        elif choice == "0":
            break

        else:
            print("Неверный ввод")

        if choice != "0" and last_message != "":
            print(last_message)
            input("\nНажмите Enter для продолжения...")
            last_message = ""


# -----------------------
# МЕНЮ БД
# -----------------------

def db_menu():
    global last_message
    while True:
        clear_console()

        print("\n--- РАБОТА С БД ---")
        print("1 - Добавить задачу")
        print("2 - Добавить сотрудника")
        print("3 - Удалить задачу")
        print("4 - Удалить сотрудника")
        print("5 - Просмотреть сотрудников")
        print("6 - Просмотреть задачи")
        print("7 - Просмотреть расписание")
        print("8 - Очистить БД")
        print("0 - Назад")

        choice = input("Выбор: ")

        if choice == "1":
            print(Fore.YELLOW + "Добавление задачи..." + Style.RESET_ALL)
            add_task()
            last_message = Fore.GREEN + "Задача добавлена" + Style.RESET_ALL

        elif choice == "2":
            print(Fore.YELLOW + "Добавление сотрудника..." + Style.RESET_ALL)
            add_employee()
            last_message = Fore.GREEN + "Сотрудник добавлен" + Style.RESET_ALL

        elif choice == "3":
            print(Fore.YELLOW + "Удаление задачи..." + Style.RESET_ALL)
            last_message = Fore.GREEN + "Задача удалена\n" + delete_task() + Style.RESET_ALL

        elif choice == "4":
            print(Fore.YELLOW + "Удаление сотрудника..." + Style.RESET_ALL)
            last_message = Fore.GREEN + "Сотрудник удален\n" + delete_employee() + Style.RESET_ALL

        elif choice == "5":
            print(Fore.YELLOW + "Просмотр сотрудников..." + Style.RESET_ALL)
            last_message = get_employees()

        elif choice == "6":
            print(Fore.YELLOW + "Просмотр задач..." + Style.RESET_ALL)
            last_message = get_tasks()

        elif choice == "7":
            print(Fore.YELLOW + "Просмотр расписания..." + Style.RESET_ALL)
            last_message =  get_schedule()

        elif choice == "8":
            print(Fore.YELLOW + "Очистка БД..." + Style.RESET_ALL)
            last_message = Fore.GREEN + "База данных очищена" + Style.RESET_ALL
            clear_db()

        elif choice == "0":
            break

        else:
            print("Неверный ввод")

        if choice != "0" and last_message != "":
            print(last_message)
            input("\nНажмите Enter для продолжения...")
            last_message = ""


def report_menu():
    global last_message
    while True:
        clear_console()

        print("\n--- ОТЧЕТЫ ---")
        print("1 - Журнал задач")
        print("0 - Назад")

        choice = input("Выбор: ")

        if choice == "1":
            print(Fore.YELLOW + "Журнал задач...\n" + Style.RESET_ALL)
            last_message = get_task_journal()

        elif choice == "0":
            break

        else:
            print("Неверный ввод")

        if choice != "0" and last_message != "":
            print(last_message)
            input("\nНажмите Enter для продолжения...")
            last_message = ""

