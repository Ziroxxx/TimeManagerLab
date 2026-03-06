import heapq
from collections import defaultdict
from colorama import init, Fore, Style

class ScheduleManager:
    def __init__(self, db):
        self.db = db
        self.tasks = self.db.get_new_tasks()
        self.employees = self.db.get_employees()

    def get_printed_schedule(self):
        self.schedule_tasks()
        return self.get_schedule_string()

    def schedule_tasks(self):
        self.tasks.sort(key=lambda x: x[2], reverse=True)

        workers = self.build_workers_heap()

        schedule = []

        max_day_capacity = max(e[2] for e in self.employees)

        for task_id, description, task_hours, status in self.tasks:

            if task_hours > 2 * max_day_capacity:
                self.schedule_parallel(task_id, task_hours, workers, schedule)
            else:
                self.schedule_single_employee(task_id, task_hours, workers, schedule)

            

        self.db.save_schedule(schedule)

    def build_workers_heap(self):
        last_slots = self.db.get_last_employee_slots()

        workers = []

        for emp_id, name, hours_per_day in self.employees:
            if emp_id in last_slots:

                day, hour = last_slots[emp_id]

                hour += 1

                if hour >= hours_per_day:
                    day += 1
                    hour = 0

                workers.append((day-1, hour, emp_id, hours_per_day))

            else:
                workers.append((0, 0, emp_id, hours_per_day))

        heapq.heapify(workers)

        return workers

    def schedule_single_employee(self, task_id, task_hours, workers, schedule):

        remaining_hours = task_hours

        day, hour, emp_id, hours_per_day = heapq.heappop(workers)

        while remaining_hours > 0:

            schedule.append({
                "task_id": task_id, 
                "employee_id": emp_id, 
                "day": day+1, 
                "hour": hour 
                })

            hour += 1
            remaining_hours -= 1

            if hour >= hours_per_day:
                day += 1
                hour = 0

        heapq.heappush(workers, (day, hour, emp_id, hours_per_day))

    def schedule_parallel(self, task_id, task_hours, workers, schedule):

        remaining_hours = task_hours

        while remaining_hours > 0:

            day, hour, emp_id, hours_per_day = heapq.heappop(workers)

            schedule.append({
                "task_id": task_id, 
                "employee_id": emp_id, 
                "day": day+1, 
                "hour": hour 
                })

            hour += 1
            remaining_hours -= 1

            if hour >= hours_per_day:
                day += 1
                hour = 0

            heapq.heappush(workers, (day, hour, emp_id, hours_per_day))

    # ---------------------
    # вывод
    # ---------------------
    def get_schedule_string(self):
        schedule_rows = self.db.get_schedule()

        if not schedule_rows:
            return None

        # собираем данные
        days = defaultdict(lambda: defaultdict(dict))
        employees = set()
        for day, hour, emp, task in schedule_rows:
            days[day][hour][emp] = task
            employees.add(emp)

        employees = sorted(list(employees))

        # определяем ширину колонок по максимальной длине текста
        col_widths = {}
        for emp in employees:
            max_len = max(
                [len(days[day][hour].get(emp, "")) for day in days for hour in days[day]] + [len(emp)]
            )
            col_widths[emp] = max_len + 2  # добавим немного отступа

        # формируем строки
        lines = [Fore.GREEN + "Расписание:" + Style.RESET_ALL]

        for day in sorted(days):
            lines.append(f"{Fore.GREEN}\nДЕНЬ {day}\n{Style.RESET_ALL}")

            # шапка
            header_parts = ["Час".ljust(4)]
            for emp in employees:
                header_parts.append(Fore.CYAN + emp.ljust(col_widths[emp]) + Style.RESET_ALL)
            header = " | ".join(header_parts)
            lines.append(header)
            lines.append("-" * (4 + 3 * len(employees) + sum(col_widths[emp] for emp in employees))) 

            # строки часов
            for hour in sorted(days[day]):
                row = f"{hour:<4} | "
                for emp in employees:
                    task = days[day][hour].get(emp, "")
                    row += task.ljust(col_widths[emp]) + " | "
                lines.append(row)

        return "\n".join(lines)