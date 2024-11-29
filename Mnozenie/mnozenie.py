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
from abc import ABC, abstractmethod
from overrides import overrides


class ITask(ABC):
    @property
    @abstractmethod
    def result(self) -> int:
        ...

    @abstractmethod
    def get_question(self) -> str:
        ...

    @property
    @abstractmethod
    def difficulty_score(self):
        ...

    @abstractmethod
    def get_time_limit(self) -> float:
        ...

    @property
    @abstractmethod
    def epoch(self) -> int:
        return self._epoch

    @epoch.setter
    @abstractmethod
    def epoch(self, epoch: int):
        self._epoch = epoch


class Mnozenie(ITask):
    _num1: int
    _num2: int
    _div: bool
    _inv: bool
    _epoch: int

    def __init__(self, num1: int, num2: int, div: bool, inv: bool, epoch: int):
        self._num1 = num1
        self._num2 = num2
        self._div = div
        self._inv = inv
        self._epoch = epoch

    @property
    @overrides
    def result(self) -> int:
        if self._div:
            if self._inv:
                return self._num1
            else:
                return self._num2
        else:
            return self._num1 * self._num2

    @overrides
    def get_question(self) -> str:
        if self._div:
            if self._inv:
                return f"{self._num1 * self._num2} / {self._num2}"
            else:
                return f"{self._num1 * self._num2} / {self._num1}"
        else:
            if self._inv:
                return f"{self._num2} x {self._num1}"
            else:
                return f"{self._num1} x {self._num2}"

    @property
    @overrides
    def difficulty_score(self):
        if self._num1 == 1 or self._num2 == 1:
            return 0
        else:
            # noinspection PyTypeChecker
            return max(1, math.log(self._num2 * self._num1 + 1) / math.log(9) + math.log(min(self._num2,  self._num1) + 1) ) - 1

    @overrides
    def get_time_limit(self) -> float:
        return 4 + self.difficulty_score * 6

    @property
    @overrides
    def epoch(self) -> int:
        return self._epoch

    @epoch.setter
    @overrides
    def epoch(self, epoch: int):
        self._epoch = epoch


class Dodawanie(ITask):
    _num1: int
    _num2: int
    _substr: bool
    _epoch: int

    def __init__(self, num1: int, num2: int, substr: bool, epoch: int):
        self._num1 = num1
        self._num2 = num2
        self._substr = substr
        self._epoch = epoch

    @property
    @overrides
    def result(self) -> int:
        if self._substr:
            return self._num1 - self._num2
        else:
            return self._num1 + self._num2

    @overrides
    def get_question(self) -> str:
        if self._substr:
            return f"{self._num1} - {self._num2}"
        else:
            return f"{self._num1} + {self._num2}"

    @property
    @overrides
    def difficulty_score(self):
        if self._num1 == 1 or self._num2 == 1:
            return 0
        else:
            # noinspection PyTypeChecker
            return max(1, math.log(self._num2 * self._num1 + 1) / math.log(9) + math.log(min(self._num2,  self._num1) + 1) ) - 1

    @overrides
    def get_time_limit(self) -> float:
        return 8 + self.difficulty_score * 30

    @property
    @overrides
    def epoch(self) -> int:
        return self._epoch

    @epoch.setter
    @overrides
    def epoch(self, epoch: int):
        self._epoch = epoch


class Tasks:
    _tasks: list[ITask]
    _epoch: int
    _performance: dict[str, list[bool]]  # mapping: question -> history of correctness of answers

    @staticmethod
    def CreateFromJSON(json_file: Path = "performance.json"):
        with open(json_file, "r") as f:
            performance = json.load(f)
        tasks = Tasks(10, 100, 10)
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
                    task = Mnozenie(i, j, False, False, 0)
                    self._tasks.append(task)
                    self._performance[task.get_question()] = [False, False, False, False]
                    task = Mnozenie(i, j, True, False, 0)
                    self._tasks.append(task)
                    self._performance[task.get_question()] = [False, False, False, False]
                    if (i != j):
                        task = Mnozenie(i, j, False, True, 0)
                        self._tasks.append(task)
                        self._performance[task.get_question()] = [False, False, False, False]
                        task = Mnozenie(i, j, True, True, 0)
                        self._tasks.append(task)
                        self._performance[task.get_question()] = [False, False, False, False]

        substr_dict = {}
        # for _ in range(500):
        #     i = random.randint(1, 100)
        #     j = random.randint(1, 100)
        #     b = random.randint(0, 3) != 1
        #     if b:
        #         key = f"{i} + {j}"
        #         if i+j > 100:
        #             continue
        #     else:
        #         if i < j:
        #             i, j = j, i
        #         key = f"{i} - {j}"
        #     if key not in substr_dict:
        #         task = Dodawanie(i, j, not b, 0)
        #         self._tasks.append(task)
        #         self._performance[task.get_question()] = [False, False, False, False]
        #         substr_dict[key] = True

    def task_fitness(self, task: ITask) -> float:
        """Returns the fitness of a task to get presented to the user based on how long it has been since it was last presented,
        and how well the user has been doing on it"""
        epoch_component = (self._epoch - task.epoch) * 0.1
        performance_last_4 = self._performance[task.get_question()][-4:]
        performance_last_4 = sum(performance_last_4) / len(performance_last_4)

        ans = (1 - performance_last_4) * (1 + epoch_component)
        random_factor = random.uniform(-0.1, 0.1)
        return -ans + random_factor

    def get_next_task(self) -> ITask:
        heap = []
        for i, task in enumerate(self._tasks):
            heappush(heap, (self.task_fitness(task), i, task))
        self._epoch += 1
        task = heappop(heap)[2]
        task.epoch = self._epoch
        return task

    def give_feedback(self, task: ITask, correct: bool):
        self._performance[task.get_question()].append(correct)
        self._performance[task.get_question()].pop(0)


class MnozenieApp:
    _tasks: Tasks
    _score: int
    _start_time: float
    _task: ITask
    _repetition: bool
    _perf_file: Path

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Mnozenie i dodawanie")

        root_path = Path(__file__).parent
        self._perf_file = root_path / "performance.json"

        if self._perf_file.exists():
            self._tasks = Tasks.CreateFromJSON(self._perf_file)
        else:
            self._tasks = Tasks(10, 100, 10)

        self._repetition = False

        self._score = 0
        self._start_time = time.time()
        self.failures = 0  # Initialize failures counter
        self.slow_responses = 0
        self.retries = 0

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

        success_image = Image.open(root_path / "success.jpg")
        self.success_photo = ImageTk.PhotoImage(success_image)

        failure_image = Image.open(root_path / "failure.png")
        self.failure_photo = ImageTk.PhotoImage(failure_image)

        timeout_image = Image.open(root_path / "timeout.png")
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
        self.window.destroy()

    def new_question(self):
        self._task = self._tasks.get_next_task()

        self.question_label['text'] = self._task.get_question() + " = ?"
        self._start_time = time.time()
        self.retries = 0

    def check_answer(self):
        answer = int(self.answer_entry.get())
        correct = answer == self._task.result
        if correct:
            if time.time() - self._start_time > self._task.get_time_limit():
                self.slow_responses += 1
                self._score += 0.1 / (1 + self.retries)
                self.show_timeout()
                self._tasks.give_feedback(self._task, False)
            else:
                self._score += 1 / (1 + self.retries)
                self.show_success()
                self._tasks.give_feedback(self._task, not self._repetition)
            self.update_gui()
            self.new_question()
            self._repetition = False
        else:
            self.failures += 1  # Increment failures counter
            self.retries += 1
            self.update_gui()
            self.show_failure(answer)
            self._repetition = True
            self._tasks.give_feedback(self._task, False)
        self._tasks.serialize_performance(self._perf_file)


    def show_success(self):
        self.success_label.pack()
        self.window.after(1000, self.success_label.pack_forget)  # Remove after 1 second

    def show_failure(self, answer):
        self.failures_label[
            'text'] = f"You answered {answer}. The correct answer to {self._task.get_question()} is {self._task.result}."
        self.failures_label.pack()
        self.window.after(1000, self.failures_label.pack_forget)  # Remove after 1 second

    def show_timeout(self):
        self.timeout_label.pack()
        self.window.after(1000, self.timeout_label.pack_forget)

    def update_gui(self):
        # Rounded to 1 digit:
        self.score_label['text'] = f"Score: {self._score:.1f}"
        self.time_label['text'] = f"Slow responses: {self.slow_responses}"
        self.failures_label['text'] = f"Failures: {self.failures}"  # Update the text of the failures label
        self.answer_entry.delete(0, 'end')
        # Add a label to display the number of failures


def main():
    app = MnozenieApp()
    app.window.mainloop()


if __name__ == "__main__":
    main()
