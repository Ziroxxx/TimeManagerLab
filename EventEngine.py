import random

class EventEngine:
    def __init__(self):
        self.delay_probability = 0.10
        self.fast_probability = 0.05
        self.sick_probability = 0.02

    def employee_event(self):
        if random.random() < self.sick_probability:
            return ("EMPLOYEE_SICK", 1)
        return None
    
    def task_event(self):
        roll = random.random()

        if roll < self.delay_probability:
            return ("TASK_DELAY", random.randint(1,3))

        if roll < self.delay_probability + self.fast_probability:
            return ("TASK_FAST", random.randint(1,2))

        return None