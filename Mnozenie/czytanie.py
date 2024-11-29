import heapq
import tkinter as tk
from dataclasses import dataclass
import json

import numpy as np
from pathlib import Path

import time

from pydub import AudioSegment
from pydub.playback import play

from .czytanie_scoring import score_sentence, calc_time_penalty
from .sound_recorder import SoundRecorder
from threading import Thread
import requests


class Speech2Text:
    def get_transcript(self, sound) -> str:
        return requests.get(
            "http://192.168.42.5:8000/request/", data=sound.json()
        ).text.strip()


@dataclass(order=True)
class Score:
    score: float
    sentence: str


class ScoringServer:
    _scores: dict[str, float]  # Sentence -> score points
    _scores_sort: list[Score]  # List of sentences sorted by score\

    def __init__(
        self,
        input_file: str = "czytanie-sentences.txt",
        output_file: str = "czytanie-scores.json",
    ):
        self._scores = {}
        self._scores_sort = []
        try:
            with open(output_file, "r") as fr:
                try:
                    self._scores = json.load(fr)
                except json.JSONDecodeError:
                    with open(output_file, "w") as fw:
                        jsonobj = json.dumps(self._scores, indent=4)
                        fw.write(jsonobj)
        except FileNotFoundError:
            with open(output_file, "w") as fw:
                jsonobj = json.dumps(self._scores, indent=4)
                fw.write(jsonobj)
        self._scores_sort = [
            Score(score, sentence) for sentence, score in self._scores.items()
        ]

        for line in open(input_file):
            sentence = line.strip()
            if sentence not in self._scores:
                self._scores[sentence] = 0
                self._scores_sort.append(Score(0, sentence))
        heapq.heapify(self._scores_sort)

    def get_sentence(self) -> str:
        return heapq.heappop(self._scores_sort).sentence

    def set_sentence_score(self, sentence: str, score: float):
        self._scores[sentence] = score
        heapq.heappush(self._scores_sort, Score(score, sentence))
        with open("czytanie-scores.json", "w") as fw:
            jsonobj = json.dumps(self._scores, indent=4)
            fw.write(jsonobj)


def get_resource(resource_name: str) -> Path:
    curdir = Path(__file__).parent
    return curdir / resource_name


class CzytanieApp:
    _window: tk.Tk
    _sound_recorder: SoundRecorder
    _scoring_server: ScoringServer
    _speech2text: Speech2Text
    _question_text: tk.Text
    _record_button: tk.Button
    _next_question_button: tk.Button
    _accuracy_score_label: tk.Label
    _total_questions_label: tk.Label
    _time_score_label: tk.Label
    _incorrect_label: tk.Label
    _correct_label: tk.Label
    accuracy_score: float
    time_score: float
    correct: float
    incorrect: float
    total_questions: float

    def __init__(self):
        self.current_sentence = None
        self.time_taken = 0.0
        self.time_start = 0.0

        self.accuracy_score = 0.0
        self.time_score = 0.0
        self.correct = 0.0
        self.incorrect = 0.0
        self.total_questions = 0.0

        self.started_recording = False
        self.answered = False
        self.rerolled = 0

        self._window = tk.Tk()
        self._window.title("Czytanie")

        self._window.configure(bg="black")

        self._user_answer = None

        self._sound_recorder = SoundRecorder()
        self._scoring_server = ScoringServer()
        self._speech2text = Speech2Text()

        try:
            with open("total_scores.json", "r") as fr:
                try:
                    scores = json.load(fr)
                except json.JSONDecodeError:
                    scores = {
                        "accuracy": 0.0,
                        "time": 0.0,
                        "correct": 0.0,
                        "incorrect": 0.0,
                        "total": 0.0,
                    }
                    with open("total_scores.json", "w") as fw:
                        jsonobj = json.dumps(scores, indent=4)
                        fw.write(jsonobj)
                self.accuracy_score = scores["accuracy"]
                self.time_score = scores["time"]
                self.correct = scores["correct"]
                self.incorrect = scores["incorrect"]
                self.total_questions = scores["total"]
        except FileNotFoundError:
            with open("total_scores.json", "w") as fw:
                jsonobj = json.dumps(
                    {
                        "accuracy": 0.0,
                        "time": 0.0,
                        "correct": 0.0,
                        "incorrect": 0.0,
                        "total": 0.0,
                    },
                    indent=4,
                )
                fw.write(jsonobj)

        self._question_text = tk.Text(
            self._window, height=1, background="black", foreground="white", width=100
        )
        self._question_text.pack()

        self._record_button = tk.Button(
            self._window, text="Record", background="black", foreground="white"
        )
        self._record_button.pack()
        self._record_button.bind("<ButtonPress>", self.start_recording)
        self._record_button.bind("<ButtonRelease>", self.stop_recording)

        self._next_question_button = tk.Button(
            self._window, text="Next question", background="black", foreground="white"
        )
        self._next_question_button.pack()
        self._next_question_button.bind("<ButtonPress>", self.next_question)

        self._accuracy_score_label = tk.Label(
            self._window,
            text=f"Accuracy score: {self.accuracy_score}",
            background="black",
            foreground="white",
        )
        self._accuracy_score_label.pack()

        self._time_score_label = tk.Label(
            self._window,
            text=f"Time score: {self.time_score}",
            background="black",
            foreground="white",
        )
        self._time_score_label.pack()

        self._correct_label = tk.Label(
            self._window,
            text=f"Correct: {self.correct}",
            background="black",
            foreground="white",
        )
        self._correct_label.pack()

        self._incorrect_label = tk.Label(
            self._window,
            text=f"Incorrect: {self.incorrect}",
            background="black",
            foreground="white",
        )
        self._incorrect_label.pack()

        self._total_questions_label = tk.Label(
            self._window,
            text=f"Total questions: {self.total_questions}",
            background="black",
            foreground="white",
        )
        self._total_questions_label.pack()

        self._user_answer = tk.Text(
            self._window, height=1, background="black", foreground="white"
        )
        self._user_answer.pack()
        self._user_answer.destroy()

        self.next_question()

    def start_recording(self, event):
        if not self.started_recording and not self.answered:
            self.started_recording = True
            self.time_taken = time.time() - self.time_start
            self._sound_recorder.start_recording()

    def stop_recording(self, event):
        if not self.answered and self.started_recording:
            self.started_recording = False
            self._sound_recorder.stop_recording()
            sound = self._sound_recorder.get_last_recording()
            if sound.length() < 1.0:
                return
            transcript = self._speech2text.get_transcript(sound)
            if transcript == "":
                return

            self.answered = True
            self.rerolled = 0
            self._record_button["state"] = "disabled"
            self._next_question_button["state"] = "normal"

            self._user_answer = tk.Text(
                self._window, height=1, background="black", foreground="white"
            )
            self._user_answer.delete("1.0", tk.END)
            self._user_answer.insert(tk.END, transcript)
            self._user_answer.pack()

            self.check_answer(transcript)

    def insert_colored_text(self, html_text):
        import re

        pattern = re.compile(r"<span style='background-color: #FF0000'>(.*?)</span>")
        last_end = 0
        self._question_text.config(
            state="normal"
        )  # Enable the Text widget before inserting text
        self._question_text.delete("1.0", tk.END)
        for match in pattern.finditer(html_text):
            self._question_text.insert(tk.END, html_text[last_end : match.start()])
            self._question_text.insert(tk.END, match.group(1), "highlight")
            last_end = match.end()
        self._question_text.insert(tk.END, html_text[last_end:])
        self._question_text.tag_config("highlight", foreground="red")
        self._question_text.config(
            state="disabled"
        )  # Disable the Text widget after inserting text

    def check_answer(self, transcript):
        score, redacted_answer_in_html = score_sentence(
            self.current_sentence, transcript
        )
        score = np.round(score, 2)
        self.accuracy_score += score
        self.accuracy_score = np.round(self.accuracy_score, 2)
        self._accuracy_score_label["text"] += f" + {score}"

        time_score = calc_time_penalty(self.time_taken, self.current_sentence)
        time_score = np.round(time_score, 2)
        self.time_score += time_score
        self._time_score_label["text"] += f" + {time_score}"

        if score == 1.0 and time_score == 1.0:
            self.correct += 1.0
            self._correct_label["text"] += " + 1"
            song = AudioSegment.from_mp3(get_resource("correct.mp3"))
            T = Thread(target=play, args=(song,))
            T.start()
        else:
            self.incorrect += 1.0
            self._incorrect_label["text"] += " + 1"
            song = AudioSegment.from_mp3(get_resource("incorrect.mp3"))
            T = Thread(target=play, args=(song,))
            T.start()

        self.total_questions += 1.0
        self._total_questions_label["text"] += " + 1"

        with open("total_scores.json", "w") as fw:
            jsonobj = json.dumps(
                {
                    "accuracy": self.accuracy_score,
                    "time": self.time_score,
                    "correct": self.correct,
                    "incorrect": self.incorrect,
                    "total": self.total_questions,
                },
                indent=4,
            )
            fw.write(jsonobj)

        self._scoring_server.set_sentence_score(self.current_sentence, score)
        self._question_text.delete("1.0", tk.END)  # Clear the existing text
        self.insert_colored_text(redacted_answer_in_html)

    def next_question(self, event=None):
        if self.rerolled < 1:  # 1 is max rerolls
            self.current_sentence = self._scoring_server.get_sentence()
            if self._user_answer is not None:
                self._user_answer.destroy()
            self.insert_colored_text(self.current_sentence)
            self.time_start = time.time()

            self._accuracy_score_label["text"] = (
                f"Accuracy score: {self.accuracy_score}"
            )
            self._time_score_label["text"] = f"Time score: {self.time_score}"
            self._correct_label["text"] = f"Correct: {int(self.correct)}"
            self._incorrect_label["text"] = f"Incorrect: {int(self.incorrect)}"
            self._total_questions_label["text"] = (
                f"Total questions: {int(self.total_questions)}"
            )

            self.answered = False
            self.started_recording = False
            self.rerolled += 1
            self._record_button["state"] = "normal"
            self._next_question_button["state"] = "disabled"


def main():
    app = CzytanieApp()
    app._window.mainloop()


if __name__ == "__main__":
    main()
