import time
import threading
import statistics
import random
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import psutil
import csv

# импортируем тестируемую функцию
from Controllers.controllers import get_schedule_for_employee as get_schedule
from Controllers.controllers import report_deviation
from Controllers.controllers import reschedule_sick
from Data.db import Database

# считываем данные для теста
db = Database("Data/schedule.db")
ids, names, _ = zip(*db.get_employees())
tids, descriptions, requireds, planneds, statuses = zip(*db.get_all_tasks())
ids = [int(i) for i in ids]
tids = [int(t) for t in tids]
db.close()

THREADS = min(len(ids), 5)  # разумное число потоков
DURATION = 30   # секунд

# worker для одного потока
def worker(employee_id, stop_time, success_times, success_lock, error_count_ref, error_lock, cpu_list, mem_list):
    local_times = []
    thread_db = Database("Data/schedule.db")  # соединение SQLite на поток

    while time.perf_counter() < stop_time:
        try:
            start = time.perf_counter()  # замер только успешного вызова

            # случайно выбираем функцию
            choice = random.choice([1, 2, 3])
            if choice == 1:
                get_schedule(employee_id, thread_db)
            elif choice == 2:
                task_id = random.choice(tids)
                deviation = random.randint(-10, 10)
                report_deviation(employee_id, thread_db, task_id, deviation)
            else:
                reschedule_sick(employee_id, thread_db)

            elapsed = time.perf_counter() - start
            local_times.append(elapsed)
            cpu_list.append(psutil.cpu_percent(interval=None))
            mem_list.append(psutil.virtual_memory().used / (1024**2))

        except sqlite3.OperationalError as e:
            # обрабатываем только "database is locked"
            if "locked" in str(e):
                with error_lock:
                    error_count_ref[0] += 1
                time.sleep(0.02)  # пауза перед новой попыткой
            else:
                # другие ошибки тоже учитываем
                with error_lock:
                    error_count_ref[0] += 1
        except Exception:
            # все остальные ошибки тоже учитываем
            with error_lock:
                error_count_ref[0] += 1

    # в конце добавляем все успешные замеры в общий список
    with success_lock:
        success_times.extend(local_times)

# запуск теста
def run_benchmark():
    success_times = []
    error_count = [0]
    success_lock = threading.Lock()
    error_lock = threading.Lock()

    cpu_usage = []
    mem_usage = []

    stop_time = time.perf_counter() + DURATION
    start_test = time.perf_counter()

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [
            executor.submit(worker, employee_id, stop_time, success_times, success_lock, error_count, error_lock, cpu_usage, mem_usage)
            for employee_id in ids
        ]
        for f in futures:
            f.result()  # чтобы увидеть исключения если есть


    total_time = time.perf_counter() - start_test
    print_stats(success_times, total_time, error_count, cpu_usage, mem_usage)

# печать статистики
def print_stats(times, total_time, error_count, cpu_usage, mem_usage):
    if not times:
        print("No successful calls were made!")
        return

    total_success = len(times)
    times.sort()

    avg = statistics.mean(times)
    min_t = times[0]
    max_t = times[-1]
    p95 = times[int(total_success * 0.95)]
    p99 = times[int(total_success * 0.99)]
    rps = total_success / total_time

    error_rate = (error_count[0] / (error_count[0] + total_success)) * 100

    print("\n===== РЕЗУЛЬТАТЫ ТЕСТА =====")
    print(f"Сотрудники (потоки): {THREADS}")
    print(f"Длительность: {total_time:.2f}s")
    print(f"Число успешных вызовов: {total_success}")
    print(f"Число ошибок: {error_count[0]}")
    print(f"Вероятность ошибки: {error_rate:.2f}%")
    print(f"RPS: {rps:.2f} calls/sec\n")
    print("Время ответа:")
    print(f"min  : {min_t*1000:.3f} ms")
    print(f"avg  : {avg*1000:.3f} ms")
    print(f"p95  : {p95*1000:.3f} ms")
    print(f"p99  : {p99*1000:.3f} ms")
    print(f"max  : {max_t*1000:.3f} ms")
    print("\nИспользование ресурсов:")
    print(f"CPU: {statistics.mean(cpu_usage):.2f}% (среднее)")
    print(f"RAM: {statistics.mean(mem_usage):.2f} MB (среднее)")

    csv_file = "benchmark_summary.csv"
    with open(csv_file, "a", newline="") as f:
        writer = csv.writer(f)
        if f.tell() == 0:  # если файл новый, пишем заголовок
            writer.writerow([
                "Threads", "Duration_s", "Total_success", "DB_errors", "Error_rate_%", "RPS",
                "Latency_min_ms", "Latency_avg_ms", "Latency_p95_ms", "Latency_p99_ms", "Latency_max_ms",
                "CPU_avg_%", "RAM_avg_MB", "Num_tasks"
            ])
        writer.writerow([
            THREADS, f"{total_time:.2f}", total_success, error_count[0], f"{error_rate:.2f}", f"{rps:.2f}",
            f"{min_t:.3f}", f"{avg:.3f}", f"{p95:.3f}", f"{p99:.3f}", f"{max_t:.3f}",
            f"{statistics.mean(cpu_usage):.2f}", f"{statistics.mean(mem_usage):.2f}", len(tids)
        ])
    print(f"\nРезультаты сохранены в {csv_file}")

if __name__ == "__main__":
    run_benchmark()