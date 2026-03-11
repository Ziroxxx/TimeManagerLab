from collections import defaultdict
from colorama import Fore, Style

class SchedulePrinter:

    def __init__(self, schedule_rows=None):
        self.schedule_rows = schedule_rows #[{"task_id": "emp_id": "day": "hour"},{},{}] vs [(), (), ()]
        self.lines = []

    def get_cache_schedule_string(schedule_cache: ScheduleCache):

        if not schedule_cache.schedule:
            return None

        days = defaultdict(lambda: defaultdict(dict))
        employees = set()

        # собираем данные
        for (day, hour), records in schedule_cache.schedule.items():
            for r in records:
                days[day][hour][r.employee_name] = r.task_name
                employees.add(r.employee_name)

        employees = sorted(list(employees))

        # определяем ширину колонок
        col_widths = {}

        for emp in employees:
            max_len = max(
                [len(days[day][hour].get(emp, "")) for day in days for hour in days[day]] + [len(emp)]
            )
            col_widths[emp] = max_len + 2

        lines = [Fore.GREEN + "Расписание:" + Style.RESET_ALL]

        for day in sorted(days):

            lines.append(f"{Fore.GREEN}\nДЕНЬ {day}\n{Style.RESET_ALL}")

            # header
            header_parts = ["Час".ljust(4)]

            for emp in employees:
                header_parts.append(Fore.CYAN + emp.ljust(col_widths[emp]) + Style.RESET_ALL)

            header = " | ".join(header_parts)
            lines.append(header)

            lines.append("-" * (4 + 3 * len(employees) + sum(col_widths[e] for e in employees)))

            # строки часов
            for hour in sorted(days[day]):

                row = f"{hour:<4} | "

                for emp in employees:
                    task = days[day][hour].get(emp, "")
                    row += task.ljust(col_widths[emp]) + " | "

                lines.append(row)

        return "\n".join(lines)