from collections import defaultdict


class TaskJournal:
    """Журнал выполнения задач."""

    def __init__(self):

        # employee_id -> [(task_id, hours), ...]
        self.logs = defaultdict(list)

        # task_id -> (status, remaining_hours)
        self.task_status = {}

    def log_work(self, employee_id, task_id, hours):

        self.logs[employee_id].append((task_id, hours))


    def update_task_status(self, task_id, status, remaining_hours):

        self.task_status[task_id] = (status, remaining_hours)
    

    def get_completed_tasks_report(self, db):

        report = []
        sum_hours = db.get_sum_hours_for_task()
        for tid, description, planned_hours, actual_hours, deviation in sum_hours:
            report.append(f"Задача {description} (ID: {tid}) планировалось часов: {planned_hours} - затрачено часов: {actual_hours} (Отклонение: {deviation})")

        return report

    def save_to_db(self, db):

        if not self.logs and not self.task_status:
            return

        if self.logs:
            db.save_log(self.logs)
            self.logs.clear()

        if self.task_status:
            db.update_tasks_bulk(self.task_status)
            self.task_status.clear()


    def reset(self):
        self.logs.clear()
        self.task_status.clear()