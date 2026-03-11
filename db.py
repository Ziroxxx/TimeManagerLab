import sqlite3


class Database:

    def __init__(self, db_name="schedule.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    # -------------------------
    # СОЗДАНИЕ ТАБЛИЦ
    # -------------------------

    def create_tables(self):

        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            hours_per_day INTEGER NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            hours_required INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'NEW'
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            employee_id INTEGER,
            day INTEGER,
            hour INTEGER,
            FOREIGN KEY(task_id) REFERENCES tasks(id),
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            task_id INTEGER NOT NULL,
            hours INTEGER NOT NULL
        )
        """)

        self.conn.commit()

    # -------------------------
    # СОТРУДНИКИ
    # -------------------------

    def add_employee(self, name, hours_per_day):

        cursor = self.conn.cursor()

        cursor.execute(
            "INSERT INTO employees(name, hours_per_day) VALUES (?, ?)",
            (name, hours_per_day)
        )

        self.conn.commit()

    def delete_employee(self, employee_id):

        cursor = self.conn.cursor()

        cursor.execute(
            "DELETE FROM employees WHERE id = ?",
            (employee_id,)
        )

        self.conn.commit()

    def get_employees(self):

        cursor = self.conn.cursor()

        cursor.execute("SELECT * FROM employees")

        return cursor.fetchall()

    def get_last_employee_slots(self):

        query = """
        SELECT employee_id, day, hour
        FROM schedule
        ORDER BY employee_id, day DESC, hour DESC
        """

        rows = self.conn.execute(query).fetchall()

        result = {}

        for emp_id, day, hour in rows:
            if emp_id not in result:
                result[emp_id] = (day, hour)

        return result

    # -------------------------
    # ЗАДАЧИ
    # -------------------------

    def add_task(self, description, hours_required):

        cursor = self.conn.cursor()

        cursor.execute(
            "INSERT INTO tasks(description, hours_required) VALUES (?, ?)",
            (description, hours_required)
        )

        self.conn.commit()

    def delete_task(self, task_id):

        cursor = self.conn.cursor()

        cursor.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,)
        )

        self.conn.commit()

    def get_all_tasks(self):

        cursor = self.conn.cursor()

        cursor.execute("SELECT * FROM tasks")

        return cursor.fetchall()

    def get_new_tasks(self):

        cursor = self.conn.cursor()

        cursor.execute("SELECT * FROM tasks WHERE status='NEW'")

        return cursor.fetchall()

    def mark_task_scheduled(self, task_id):

        cursor = self.conn.cursor()

        cursor.execute(
            "UPDATE tasks SET status='SCHEDULED' WHERE id=?",
            (task_id,)
        )

        self.conn.commit()

    def update_task_status_bulk(self, task_status: dict):
        """
        task_status: {task_id: status}
        """

        if not task_status:
            return

        case_statements = []
        params = []
        ids = []

        for task_id, status in task_status.items():

            case_statements.append("WHEN id = ? THEN ?")
            params.extend([task_id, status])
            ids.append(task_id)

        sql = f"""
            UPDATE tasks
            SET status = CASE
                {' '.join(case_statements)}
            END
            WHERE id IN ({','.join(['?'] * len(ids))})
        """

        params.extend(ids)

        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        self.conn.commit()

    # ------------------------------------------------
    # РАСПИСАНИЕ
    # ------------------------------------------------

    def add_schedule_record(self, task_id, employee_id, day, hour):

        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO schedule(task_id, employee_id, day, hour)
            VALUES (?, ?, ?, ?)
            """,
            (task_id, employee_id, day, hour)
        )

        self.conn.commit()

    def get_schedule(self):

        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT s.day, s.hour, e.name, t.description
        FROM schedule s
        JOIN employees e ON s.employee_id = e.id
        JOIN tasks t ON s.task_id = t.id
        ORDER BY s.day, s.hour
        """)

        return cursor.fetchall()
    
    def get_detailed_schedule(self):

        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT
        s.day,
        s.hour,
        e.id,
        e.name,
        t.id,
        t.description,
        t.hours_required,
        t.status
        FROM schedule s
        JOIN employees e ON s.employee_id = e.id
        JOIN tasks t ON s.task_id = t.id
        ORDER BY s.day, s.hour
        """)

        return cursor.fetchall()

    def save_schedule(self, schedule):

        scheduled_tasks = set()

        with self.conn:

            for row in schedule:

                self.add_schedule_record(
                    row["task_id"],
                    row["employee_id"],
                    row["day"],
                    row["hour"]
                )

                scheduled_tasks.add(row["task_id"])

            for task_id in scheduled_tasks:
                self.mark_task_scheduled(task_id)
                
    def clear_schedule(self):

        cursor = self.conn.cursor()

        cursor.execute("DELETE FROM schedule")

        self.conn.commit()

    def get_schedule_days(self):

        cursor = self.conn.cursor()

        cursor.execute("SELECT MAX(day) FROM schedule")

        result = cursor.fetchone()

        return result[0] if result and result[0] else 0
    
    def delete_future_schedule(self, day, hour):
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM schedule
            WHERE day > ?
            OR (day = ? AND hour >= ?)
        """, (day, day, hour))
        self.conn.commit()

    def resave_schedule(self, schedule: list):
        """
        Сохраняет список словарей вида {"task_id": ..., "employee_id": ..., "day": ..., "hour": ...}
        """
        if not schedule:
            return

        cursor = self.conn.cursor()
        records = [(s["task_id"], s["employee_id"], s["day"], s["hour"]) for s in schedule]

        cursor.executemany("""
            INSERT INTO schedule(task_id, employee_id, day, hour)
            VALUES (?, ?, ?, ?)
        """, records)

        self.conn.commit()
    
    # -------------------------
    # ЛОГИ ВЫПОЛНЕНИЯ
    # -------------------------
    def save_log(self, logs):
        """
        logs: defaultdict(list) -> employee_id : [(task_id, hours), ...]
        """
        rows = []
        for emp_id, entries in logs.items():
            for task_id, hours in entries:
                rows.append((emp_id, task_id, hours))

        if not rows:
            return

        cursor = self.conn.cursor()
        cursor.executemany(
            """
            INSERT INTO task_logs(employee_id, task_id, hours)
            VALUES (?, ?, ?)
            """,
            rows
        )
        self.conn.commit()

    def clear_logs(self):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            DELETE FROM task_logs
            """
        )

        self.conn.commit()

    # -------------------------
    # ОЧИСТКА БД
    # -------------------------

    def clear_db(self):

        cursor = self.conn.cursor()

        cursor.execute("DELETE FROM schedule")
        cursor.execute("DELETE FROM employees")
        cursor.execute("DELETE FROM tasks")
        cursor.execute("DELETE FROM task_logs")
        
        self.conn.commit()

    # -------------------------
    # ЗАКРЫТИЕ
    # -------------------------

    def close(self):
        self.conn.close()