from collections import defaultdict

class ScheduleCache:

    def __init__(self, rows):

        self.schedule = defaultdict(list)
        self.task_dict = {}

        for row in rows:

            task_id = row[4]

            if task_id not in self.task_dict:
                self.task_dict[task_id] = {
                    "task_name": row[5],
                    "remaining_hours": row[6],
                    "planned_hours": row[6],
                    "status": row[7]
                }

            record = ScheduleRecord(
                day=row[0],
                hour=row[1],
                employee_id=row[2],
                employee_name=row[3],
                task_id=row[4],
                task_name=row[5],
            )

            self.schedule[(record.day, record.hour)].append(record)

    def get(self, day, hour):

        return self.schedule.get((day, hour), [])

    def get_hours_for_day(self, day):

        hours = set()

        for (d, h) in self.schedule.keys():

            if d == day:
                hours.add(h)

        return sorted(hours)

    def get_employees_for_day(self, day):

        employees = {}

        for (d, h), records in self.schedule.items():

            if d != day:
                continue

            for r in records:
                employees[r.employee_id] = r.employee_name

        return employees

class ScheduleRecord:

    def __init__(self, day, hour, employee_id, employee_name,
                 task_id, task_name):

        self.day = day
        self.hour = hour

        self.employee_id = employee_id
        self.employee_name = employee_name

        self.task_id = task_id
        self.task_name = task_name
