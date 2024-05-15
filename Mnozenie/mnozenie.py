# A simple program that teaches young children multiplication table.
#
# The main goal is to set a time limit for each question and to keep track of the number of correct answers.
#

from heapq import heappush, heappop

import tkinter as tk
import random
import time
import math
from PIL import Image, ImageTk
from pathlib import Path
import json


class Task:
    _num1: int
    _num2: int
    _epoch: int

    def __init__(self, num1: int, num2: int, epoch: int):
        self._num1 = num1
        self._num2 = num2
        self._epoch = epoch

    @property
    def result(self) -> int:
        return self._num1 * self._num2

    @property
    def num1(self) -> int:
        return self._num1

    @property
    def num2(self) -> int:
        return self._num2

    def get_question(self, bInverse: bool) -> str:
        if bInverse:
            return f"{self._num2} x {self._num1}"
        else:
            return f"{self._num1} x {self._num2}"

    @property
    def difficulty_score(self):
        if self._num1 == 1 or self._num2 == 1:
            return 0
        else:
            # noinspection PyTypeChecker
            return max(1, math.log(self.result + 1) / math.log(9)) - 1

    def get_time_limit(self) -> float:
        return 7 + self.difficulty_score * 18

    @property
    def epoch(self) -> int:
        return self._epoch

    def set_epoch(self, epoch: int):
        self._epoch = epoch


class Tasks:
    _tasks: list[Task]
    _epoch: int
    _performance: dict[str, list[bool]]  # mapping: question -> history of correctness of answers

    @staticmethod
    def CreateFromJSON(json_file: Path = "performance.json"):
        with open(json_file, "r") as f:
            performance = json.load(f)
        tasks = Tasks(10, 50, 10)
        tasks._performance = performance
        for question, history in performance.items():
            tasks._performance[question] = [bool(x) for x in history]
        return tasks

    def serialize_performance(self, json_file: Path = "performance.json"):
        with open(json_file, "w") as f:
            json.dump(self._performance, f)

    def __init__(self, max_num: int, max_result: float, min_result: float):
        self._tasks = []
        self._performance = {}
        self._epoch = 0
        for i in range(1, max_num):
            for j in range(i, max_num):
                if i * j <= max_result and i * j >= min_result:
                    task = Task(i, j, 0)
                    self._tasks.append(task)
                    self._performance[task.get_question(False)] = [False, False, False, False]

    def task_fitness(self, task: Task) -> float:
        """Returns the fitness of a task to get presented to the user based on how long it has been since it was last presented,
        and how well the user has been doing on it"""
        epoch_component = (self._epoch - task.epoch) * 0.1
        performance_last_4 = self._performance[task.get_question(False)][-4:]
        performance_last_4 = sum(performance_last_4) / len(performance_last_4)

        ans = (1 - performance_last_4) * (1 + epoch_component)
        random_factor = random.uniform(-0.1, 0.1)
        return -ans + random_factor

    def get_next_task(self) -> Task:
        heap = []
        for i, task in enumerate(self._tasks):
            heappush(heap, (self.task_fitness(task), i, task))
        self._epoch += 1
        task = heappop(heap)[2]
        task.set_epoch(self._epoch)
        return task

    def give_feedback(self, task: Task, correct: bool):
        self._performance[task.get_question(False)].append(correct)
        self._performance[task.get_question(False)].pop(0)


class MnozenieApp:
    _tasks: Tasks
    _score: int
    _start_time: float
    _task: Task
    _task_inv: bool
    _repetition: bool

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Mnozenie")

        json_file = Path("performance.json")
        if not json_file.exists():
            self._tasks = Tasks.CreateFromJSON()
        else:
            self._tasks = Tasks(10, 50, 10)

        self._repetition = False

        self._score = 0
        self._start_time = time.time()
        self.failures = 0  # Initialize failures counter
        self.slow_responses = 0

        self.question_label = tk.Label(self.window, text="")
        self.question_label.pack()

        self.answer_entry = tk.Entry(self.window)
        self.answer_entry.pack()
        self.answer_entry.focus_set()  # Set focus on the textbox

        self.check_button = tk.Button(self.window, text="Check Answer", command=self.check_answer)
        self.check_button.pack()

        self.quit_button = tk.Button(self.window, text="Quit", command=self.quit_app)
        self.quit_button.pack()

        self.score_label = tk.Label(self.window, text="Score: 0")
        self.score_label.pack()

        self.time_label = tk.Label(self.window, text="Time: 0")
        self.time_label.pack()

        self.window.bind('<Return>', lambda event: self.check_answer())
        self.window.bind('<KP_Enter>', lambda event: self.check_answer())  # Bind the numeric pad enter key

        success_image = Image.open("success.jpg")
        self.success_photo = ImageTk.PhotoImage(success_image)

        failure_image = Image.open("failure.png")
        self.failure_photo = ImageTk.PhotoImage(failure_image)

        timeout_image = Image.open("timeout.png")
        self.timeout_photo = ImageTk.PhotoImage(timeout_image)

        # Create labels for images
        self.success_label = tk.Label(self.window, image=self.success_photo)
        # self.failure_label = tk.Label(self.window, image=self.failure_photo)
        # self.timeout_label = tk.Label(self.window, image=self.timeout_photo)
        # self.success_label = tk.Label(self.window)
        self.failures_label = tk.Label(self.window, text=f"Failures: {self.failures}")
        self.failures_label.pack()
        self.timeout_label = tk.Label(self.window)

        self.new_question()

    def quit_app(self):
        self._tasks.serialize_performance()
        self.window.destroy()

    def new_question(self):
        self._task = self._tasks.get_next_task()
        self._task_inv = random.choice([True, False])
        if self._task_inv:
            num1 = self._task.num1
            num2 = self._task.num2
        else:
            num1 = self._task.num2
            num2 = self._task.num1

        self.question_label['text'] = f"{num1} x {num2} = ?"
        self._start_time = time.time()

    def check_answer(self):
        answer = int(self.answer_entry.get())
        correct = answer == self._task.result
        if correct:
            if time.time() - self._start_time > self._task.get_time_limit():
                self.slow_responses += 1
                self.show_timeout()
                self._tasks.give_feedback(self._task, False)
            else:
                self._score += 1
                self.show_success()
                self._tasks.give_feedback(self._task, not self._repetition)
            self.update_gui()
            self.new_question()
            self._repetition = False
        else:
            self.failures += 1  # Increment failures counter
            self.update_gui()
            self.show_failure(answer)
            self._repetition = True
            self._tasks.give_feedback(self._task, False)

    def show_success(self):
        self.success_label.pack()
        self.window.after(1000, self.success_label.pack_forget)  # Remove after 1 second

    def show_failure(self, answer):
        self.failure_label[
            'text'] = f"You answered {answer}. The correct answer to {self._task.get_question(self._task_inv)} is {self._task.result}."
        self.failure_label.pack()
        self.window.after(1000, self.failure_label.pack_forget)  # Remove after 1 second

    def show_timeout(self):
        self.timeout_label.pack()
        self.window.after(1000, self.timeout_label.pack_forget)

    def update_gui(self):
        self.score_label['text'] = f"Score: {self._score}"
        self.time_label['text'] = f"Slow responses: {self.slow_responses}"
        self.failures_label['text'] = f"Failures: {self.failures}"  # Update the text of the failures label
        self.answer_entry.delete(0, 'end')
        # Add a label to display the number of failures


if __name__ == "__main__":
    app = MnozenieApp()
    app.window.mainloop()
