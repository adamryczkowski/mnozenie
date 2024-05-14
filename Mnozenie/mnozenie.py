# A simple program that teaches young children multiplication table.
#
# The main goal is to set a time limit for each question and to keep track of the number of correct answers.
#

import tkinter as tk
import random
import time
import math
from PIL import Image, ImageTk

class MnozenieApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Mnozenie")

        self.score = 0
        self.start_time = time.time()
        self.time_limit = 10  # seconds
        self.failures = 0  # Initialize failures counter
        self.slow_responses = 0

        self.question_label = tk.Label(self.window, text="")
        self.question_label.pack()

        self.answer_entry = tk.Entry(self.window)
        self.answer_entry.pack()
        self.answer_entry.focus_set()  # Set focus on the textbox



        self.check_button = tk.Button(self.window, text="Check Answer", command=self.check_answer)
        self.check_button.pack()

        self.score_label = tk.Label(self.window, text="Score: 0")
        self.score_label.pack()

        self.time_label = tk.Label(self.window, text="Time: 0")
        self.time_label.pack()

        self.window.bind('<Return>', lambda event: self.check_answer())


        success_image = Image.open("success.jpg")
        self.success_photo = ImageTk.PhotoImage(success_image)

        failure_image = Image.open("failure.png")
        self.failure_photo = ImageTk.PhotoImage(failure_image)

        timeout_image = Image.open("timeout.png")
        self.timeout_photo = ImageTk.PhotoImage(timeout_image)

        # Create labels for images
        self.success_label = tk.Label(self.window, image=self.success_photo)
        self.failure_label = tk.Label(self.window, image=self.failure_photo)
        self.timeout_label = tk.Label(self.window, image=self.timeout_photo)


        self.new_question()

    def new_question(self):
        self.num1 = random.randint(1, 9)
        self.num2 = random.randint(1, 9)
        self.question_label['text'] = f"{self.num1} x {self.num2} = ?"
        self.start_time = time.time()
        result = self.num1 * self.num2
        if self.num1 == 1 or self.num2 == 1:
            self.difficulty_score = 0
        else:
            self.difficulty_score = (max(1, math.log(result + 1)/math.log(9)) - 1)

        self.time_limit = 3 + self.difficulty_score * 12


    def check_answer(self):
        answer = int(self.answer_entry.get())
        correct = answer == self.num1 * self.num2
        if correct:
            if time.time() - self.start_time > self.time_limit:
                self.slow_responses += 1
                self.show_timeout()
            else:
                self.score += 1
                self.show_success()
        else:
            self.failures += 1  # Increment failures counter
            self.show_failure()
        self.update_gui()
        self.new_question()

    def show_success(self):
        self.success_label.pack()
        self.window.after(1000, self.success_label.pack_forget)  # Remove after 1 second

    def show_failure(self):
        self.failure_label.pack()
        self.window.after(1000, self.failure_label.pack_forget)  # Remove after 1 second

    def show_timeout(self):
        self.timeout_label.pack()
        self.window.after(1000, self.timeout_label.pack_forget)

    def update_gui(self):
        self.score_label['text'] = f"Score: {self.score}"
        self.time_label['text'] = f"Slow responses: {self.slow_responses}"
        self.answer_entry.delete(0, 'end')

        # Add a label to display the number of failures
        self.failures_label = tk.Label(self.window, text=f"Failures: {self.failures}")
        self.failures_label.pack()

if __name__ == "__main__":
    app = MnozenieApp()
    app.window.mainloop()