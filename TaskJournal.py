from collections import defaultdict


class TaskJournal:
    """Журнал выполнения задач."""

    def __init__(self):

        # employee_id -> [(task_id, hours)]
        self.logs = defaultdict(list)

        # task_id -> status
        self.task_status = {}

    def log_work(self, employee_id, task_id, hours):

        self.logs[employee_id].append((task_id, hours))


    def update_task_status(self, task_id, status):

        self.task_status[task_id] = status


    def save_to_db(self, db):

        if not self.logs and not self.task_status:
            return

        if self.logs:
            db.save_log(self.logs)
            self.logs.clear()

        if self.task_status:
            db.update_task_status_bulk(self.task_status)
            self.task_status.clear()


    def reset(self):
        self.logs.clear()
        self.task_status.clear()