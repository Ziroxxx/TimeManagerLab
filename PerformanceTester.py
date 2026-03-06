import time
import csv
import os
from colorama import init, Fore, Style

class PerformanceTester:

    def __init__(self, db, data_generator, schedule_manager_class):
        self.db = db
        self.data_generator = data_generator
        self.schedule_manager_class = schedule_manager_class

    def prepare_csv(self, file_name="performance_results.csv"):

        file_exists = os.path.exists(file_name)

        if not file_exists:
            with open(file_name, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "run",
                    "num_tasks",
                    "num_employees",
                    "total_task_hours",
                    "avg_task_hours",
                    "avg_employee_hours",
                    "schedule_days",
                    "tasks_per_sec",
                    "elapsed_sec",
                ])

    def collect_metrics(self, num_tasks, num_employees, elapsed):

        tasks = self.db.get_all_tasks()
        employees = self.db.get_employees()

        total_task_hours = sum(t[2] for t in tasks)
        avg_task_hours = total_task_hours / len(tasks)

        avg_employee_hours = sum(e[2] for e in employees) / len(employees)

        schedule_days = self.db.get_schedule_days()

        tasks_per_sec = num_tasks / elapsed if elapsed > 0 else 0

        return (
            total_task_hours,
            avg_task_hours,
            avg_employee_hours,
            schedule_days,
            tasks_per_sec
        )

    def run_test(
        self,
        num_runs,
        num_tasks,
        task_hours_min,
        task_hours_max,
        num_employees,
        emp_hours_min,
        emp_hours_max
    ):

        self.db.clear_db()

        self.data_generator.generate_employees(
            num_employees,
            emp_hours_min,
            emp_hours_max
        )

        self.data_generator.generate_tasks(
            num_tasks,
            task_hours_min,
            task_hours_max
        )

        self.prepare_csv()

        manager = self.schedule_manager_class(self.db)

        timings = []

        for run in range(1, num_runs + 1):

            start = time.perf_counter()

            manager.get_printed_schedule()

            end = time.perf_counter()

            elapsed = end - start
            timings.append(elapsed)

            metrics = self.collect_metrics(
                num_tasks,
                num_employees,
                elapsed
            )

            with open("performance_results.csv", "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                writer.writerow([
                    run,
                    num_tasks,
                    num_employees,
                    *metrics,
                    f"{elapsed:.4f}"
                ])

            self.db.clear_schedule()

            print(f"\nПрогон {run}: {Fore.CYAN}{elapsed:.4f}{Style.RESET_ALL} секунд")

        avg_time = sum(timings) / len(timings)

        return avg_time