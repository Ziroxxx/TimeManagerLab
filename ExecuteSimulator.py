from ScheduleDTO import *
from colorama import Fore, Style
from Rescheduler import Rescheduler

class ExecuteSimulator:

    def __init__(self, db, event_engine, journal):

        self.db = db
        self.event_engine = event_engine
        self.journal = journal

        self.result = []
        self.rescheduler = None 

    def simulate(self, days):

        self.db.clear_logs()
        rows = self.db.get_detailed_schedule()

        if not rows:
            self.result.append("Расписание пустое")
            return "\n".join(self.result)

        schedule = ScheduleCache(rows)
        self.rescheduler = Rescheduler(self.db, schedule, sim_day=1, sim_hour=0, sick_today=set())

        for day in range(1, days + 1):

            self.result.append(Fore.CYAN + f"\n===== День {day} =====" + Style.RESET_ALL)

            sick_today = set()

            employees = schedule.get_employees_for_day(day)

            # проверка болезней
            for emp_id, emp_name in employees.items():

                event = self.event_engine.employee_event()

                if event and event[0] == "EMPLOYEE_SICK":

                    sick_today.add(emp_id)

                    self.result.append(Fore.RED + f"{emp_name} заболел и пропускает день" + Style.RESET_ALL)

            if sick_today:
                self.rescheduler.sim_day = day
                self.rescheduler.sim_hour = 0
                self.rescheduler.sick_today = sick_today

                schedule = self.rescheduler.rebuild_schedule()
                self.rescheduler.old_schedule = schedule
                self.result.append(Fore.YELLOW + "Перестройка расписания, из-за заболевших сотрудников сегодня..." + Style.RESET_ALL)

            hour_index = 0
            hours = schedule.get_hours_for_day(day)

            while hour_index < len(hours):
                hour = hours[hour_index]

                self.result.append(f"\n-- Час {hour} --")

                records_for_day_hour = schedule.get(day, hour)

                rebuild_needed = False

                for slot in records_for_day_hour:
                    task = schedule.task_dict[slot.task_id]

                    if slot.employee_id in sick_today:
                        continue

                    if task["status"] == "COMPLETED":
                        continue

                    # события задачи
                    event = self.event_engine.task_event()

                    if event:
                        event_type, value = event
                        if event_type == "TASK_DELAY":
                            task["remaining_hours"] += value
                            rebuild_needed = True
                            self.result.append(Fore.YELLOW + f"{slot.task_name} оказалась сложнее (+{value}ч)" + Style.RESET_ALL)
                        elif event_type == "TASK_FAST":
                            task["remaining_hours"] = max(0, task["remaining_hours"] - value)
                            rebuild_needed = True
                            self.result.append(Fore.YELLOW + f"{slot.task_name} оказалась проще (-{value}ч)" + Style.RESET_ALL)

                    # выполняем час работы
                    self.journal.log_work(slot.employee_id, slot.task_id, 1)
                    task = schedule.task_dict[slot.task_id]
                    task["remaining_hours"] -= 1

                    if task["status"] == "SCHEDULED":
                        task["status"] = "IN_PROGRESS"
                        self.journal.update_task_status(slot.task_id, "IN_PROGRESS")

                    if task["remaining_hours"] <= 0:
                        task["remaining_hours"] = 0
                        task["status"] = "COMPLETED"
                        self.journal.update_task_status(slot.task_id, "COMPLETED")

                    self.result.append(
                        f"{slot.employee_name} работает над '{slot.task_name}' "
                        f"(осталось {task["remaining_hours"]})"
                    )

                if rebuild_needed:
                    self.rescheduler.sim_day = day
                    self.rescheduler.sim_hour = hour+1
                    self.rescheduler.sick_today = sick_today

                    schedule = self.rescheduler.rebuild_schedule()
                    hours = schedule.get_hours_for_day(day)
                    print(hours)
                    self.rescheduler.old_schedule = schedule

                    self.result.append(
                        Fore.YELLOW + "Перестройка расписания из-за изменений задач" + Style.RESET_ALL
                    )
                
                hour_index += 1

        self.result.append(Fore.GREEN + "\nСимуляция завершена\n" + Style.RESET_ALL)

        self.journal.save_to_db(self.db)

        self.result.append(Fore.GREEN + "Логи выполнения сохранены" + Style.RESET_ALL)

        if self.rescheduler:
            self.rescheduler.save_schedule_to_db()
            self.result.append(Fore.GREEN + "Перепланированное расписание сохранено в БД" + Style.RESET_ALL)
        return "\n".join(self.result)