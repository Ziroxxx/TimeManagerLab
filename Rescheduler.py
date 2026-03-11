import heapq
from collections import defaultdict
from ScheduleDTO import ScheduleCache, ScheduleRecord

class Rescheduler:
    """
    Перепланирование расписания на основе старого ScheduleCache.
    Поддерживает:
      - пропуск больных сотрудников
      - распределение задач на одного или нескольких сотрудников
      - сохранение выполненных часов
    """

    def __init__(self, db, old_schedule: ScheduleCache, sim_day=1, sim_hour=0, sick_today=None):
        self.db = db
        self.old_schedule = old_schedule
        self.sim_day = sim_day
        self.sim_hour = sim_hour
        self.sick_today = set(sick_today) if sick_today else set()
        self.new_slots = []
        self.employees = db.get_employees()  # [(emp_id, name, hours_per_day)]

    # -------------------------
    # Основной метод перепланирования
    # -------------------------
    def rebuild_schedule(self):
        self.new_slots = []
        self._cut_future_schedule()

        # 1) Собираем оставшиеся задачи
        tasks = self._collect_remaining_tasks()
        if not tasks:
            return self.old_schedule

        # 2) Строим кучу сотрудников с учётом текущей доступности
        workers = self._build_workers_heap()
        if not workers:
            return self.old_schedule

        max_day_capacity = max(e[2] for e in self.employees)

        # 3) Планируем задачи
        for task in tasks:
            if task["remaining_hours"] > 2 * max_day_capacity:
                self._schedule_parallel(task, workers)
            else:
                self._schedule_single(task, workers)

        # 4) Собираем новый ScheduleCache
        return self._build_new_cache()

    # -------------------------
    # Сбор оставшихся задач
    # -------------------------
    def _collect_remaining_tasks(self):
        tasks = []
        for task_id, t in self.old_schedule.task_dict.items():
            if t["remaining_hours"] > 0:
                tasks.append({
                    "task_id": task_id,
                    "task_name": t.get("task_name", f"Task #{task_id}"),
                    "remaining_hours": t["remaining_hours"],
                    "planned_hours": t["planned_hours"],
                    "status": t.get("status", "SCHEDULED")
                })
        # сортируем по оставшимся часам (LPT — Longest Processing Time)
        tasks.sort(key=lambda x: x["remaining_hours"], reverse=True)
        return tasks

    # -------------------------
    # Построение кучи сотрудников по их следующей доступности
    # -------------------------
    def _build_workers_heap(self):

        last_slots = self._get_last_slots_before_sim()
        workers = []

        for emp_id, name, hours_per_day in self.employees:

            if emp_id in self.sick_today:
                continue

            if emp_id in last_slots:

                last_day, last_hour = last_slots[emp_id]

                if last_day < self.sim_day:
                    start_day = self.sim_day
                    start_hour = self.sim_hour
                    worked_today = 0

                elif last_day == self.sim_day and last_hour < self.sim_hour:
                    start_day = self.sim_day
                    start_hour = self.sim_hour
                    worked_today = last_hour + 1

                else:
                    start_day = last_day
                    start_hour = last_hour + 1
                    worked_today = last_hour + 1

                    if start_hour >= hours_per_day:
                        start_day += 1
                        start_hour = 0
                        worked_today = 0

            else:
                start_day = self.sim_day
                start_hour = self.sim_hour
                worked_today = 0

            workers.append((start_day, start_hour, emp_id, hours_per_day, worked_today))

        heapq.heapify(workers)

        return workers
    def _cut_future_schedule(self):

        new_schedule = {}

        for (day, hour), records in self.old_schedule.schedule.items():

            if day < self.sim_day:
                new_schedule[(day, hour)] = records

            elif day == self.sim_day and hour <= self.sim_hour:
                new_schedule[(day, hour)] = records

        self.old_schedule.schedule = new_schedule
    
    def _get_last_slots_before_sim(self):

        last = {}

        for (day, hour), records in self.old_schedule.schedule.items():

            if day > self.sim_day:
                continue

            if day == self.sim_day and hour >= self.sim_hour:
                continue

            for r in records:
                last[r.employee_id] = (day, hour)

        return last

    # -------------------------
    # Назначение задачи одному сотруднику
    # -------------------------
    def _schedule_single(self, task, workers):

        remaining = task["remaining_hours"]

        day, hour, emp_id, hours_per_day, worked_today = heapq.heappop(workers)

        while remaining > 0:

            self.new_slots.append({
                "task_id": task["task_id"],
                "employee_id": emp_id,
                "day": day,
                "hour": hour
            })

            remaining -= 1
            hour += 1
            worked_today += 1

            if worked_today >= hours_per_day:
                day += 1
                hour = 0
                worked_today = 0

        heapq.heappush(workers, (day, hour, emp_id, hours_per_day, worked_today))

    # -------------------------
    # Назначение задачи на нескольких сотрудников
    # -------------------------
    def _schedule_parallel(self, task, workers):

        remaining = task["remaining_hours"]

        while remaining > 0:

            day, hour, emp_id, hours_per_day, worked_today = heapq.heappop(workers)

            self.new_slots.append({
                "task_id": task["task_id"],
                "employee_id": emp_id,
                "day": day,
                "hour": hour
            })

            remaining -= 1
            hour += 1
            worked_today += 1

            if worked_today >= hours_per_day:
                day += 1
                hour = 0
                worked_today = 0

            heapq.heappush(workers, (day, hour, emp_id, hours_per_day, worked_today))

    # -------------------------
    # Построение нового ScheduleCache
    # -------------------------
    def _build_new_cache(self):
        emp_dict = {emp_id: name for emp_id, name, _ in self.employees}

        # Карта task_id -> имя задачи
        task_name_map = {tid: rec.task_name for recs in self.old_schedule.schedule.values() for rec in recs for tid in [rec.task_id]}

        rows = []
        for slot in self.new_slots:
            employee_name = emp_dict.get(slot["employee_id"], "Unknown")
            task_name = task_name_map.get(slot["task_id"], f"Task #{slot['task_id']}")
            # берем текущее состояние задачи из старого ScheduleCache
            task_info = self.old_schedule.task_dict.get(slot["task_id"], {})
            remaining_hours = task_info.get("remaining_hours", task_info.get("planned_hours", 0))
            status = task_info.get("status", "SCHEDULED")

            rows.append((
                slot["day"],
                slot["hour"],
                slot["employee_id"],
                employee_name,
                slot["task_id"],
                task_name,
                remaining_hours,
                status
            ))

        new_cache = ScheduleCache(rows)
        return new_cache

    # -------------------------
    # Сохранение перепланированного расписания в БД
    # -------------------------
    def save_schedule_to_db(self):
        self.db.delete_future_schedule(self.sim_day, self.sim_hour)
        self.db.resave_schedule(self.new_slots)
        self.new_slots = []