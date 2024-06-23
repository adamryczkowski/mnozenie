import heapq
import tkinter as tk
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

import whisper
import time

from czytanie_scoring import score_sentence, calc_time_penalty
from sound_recorder import SoundRecorder


class Speech2Text:
    _model: whisper.model

    def __init__(self):
        self._model = whisper.load_model("medium")

    def get_transcript(self, sound) -> str:
        out = self._model.transcribe(sound, language='pl')['text'].strip()
        return out


@dataclass(order=True)
class Sentence:
    score: float
    sentence: str = field(compare=False)


class ScoringServer:
    _scores: dict[str, Sentence]  # Sentence -> score points
    _scores_inv: list[Sentence]  # list of sentences sorted by score points

    def __init__(self, input_file: str = "czytanie-sentences.txt"):
        self._scores = {}
        for line in open(input_file):
            sentence = line.strip()
            self._scores[sentence] = Sentence(0, sentence)
        self._scores_inv = list(self._scores.values())
        heapq.heapify(self._scores_inv)

    def get_sentence(self) -> str:
        return heapq.heappop(self._scores_inv).sentence

    def set_sentence_score(self, sentence: str, score: float):
        self._scores[sentence].score = score
        heapq.heappush(self._scores_inv, self._scores[sentence])

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

    def __init__(self):
        self.current_sentence = None
        self.time_taken = 0
        self.time_start = 0

        self.accuracy_score = 0
        self.time_score = 0
        self.correct = 0
        self.incorrect = 0
        self.total_questions = 0

        self.answered = False
        self.rerolled = 0

        self._window = tk.Tk()
        self._window.title("Czytanie")

        self._window.configure(bg='black')

        self._user_answer = None

        self._sound_recorder = SoundRecorder()
        self._scoring_server = ScoringServer()
        self._speech2text = Speech2Text()

        self._question_text = tk.Text(self._window, height=1, background='black', foreground='white')
        self._question_text.pack()

        self._record_button = tk.Button(self._window, text="Record", background='black', foreground='white')
        self._record_button.pack()
        self._record_button.bind("<ButtonPress>", self.start_recording)
        self._record_button.bind("<ButtonRelease>", self.stop_recording)

        self._next_question_button = tk.Button(self._window, text="Next question", background='black',
                                               foreground='white')
        self._next_question_button.pack()
        self._next_question_button.bind("<ButtonPress>", self.next_question)

        self._accuracy_score_label = tk.Label(self._window, text=f"Accuracy score: {self.accuracy_score}", background='black',
                                              foreground='white')
        self._accuracy_score_label.pack()

        self._time_score_label = tk.Label(self._window, text=f"Time score: {self.time_score}", background='black', foreground='white')
        self._time_score_label.pack()

        self._correct_label = tk.Label(self._window, text=f"Correct: {self.correct}", background='black', foreground='white')
        self._correct_label.pack()

        self._incorrect_label = tk.Label(self._window, text=f"Incorrect: {self.incorrect}", background='black', foreground='white')
        self._incorrect_label.pack()

        self._total_questions_label = tk.Label(self._window, text=f"Total questions: {self.total_questions}", background='black',
                                               foreground='white')
        self._total_questions_label.pack()

        self._user_answer = tk.Text(self._window, height=1, background='black', foreground='white')
        self._user_answer.pack()
        self._user_answer.destroy()

        self.next_question()

    def start_recording(self, event):
        if not self.answered:
            self.time_taken = time.time() - self.time_start
            self._sound_recorder.start_recording()

    def stop_recording(self, event):
        self._sound_recorder.stop_recording()
        sound = self._sound_recorder.get_last_recording_as_whisper_sound()
        transcript = self._speech2text.get_transcript(sound)
        if transcript == "":
            return

        self._user_answer = tk.Text(self._window, height=1, background='black', foreground='white')
        self._user_answer.delete('1.0', tk.END)
        self._user_answer.insert(tk.END, transcript)
        self._user_answer.pack()

        self.check_answer(transcript)

        self.answered = True
        self.rerolled = 0
        self._record_button['state'] = 'disabled'
        self._next_question_button['state'] = 'normal'

    def insert_colored_text(self, html_text):
        import re
        pattern = re.compile(r"<span style='background-color: #FF0000'>(.*?)</span>")
        last_end = 0
        self._question_text.config(state='normal')  # Enable the Text widget before inserting text
        self._question_text.delete('1.0', tk.END)
        for match in pattern.finditer(html_text):
            self._question_text.insert(tk.END, html_text[last_end:match.start()])
            self._question_text.insert(tk.END, match.group(1), 'highlight')
            last_end = match.end()
        self._question_text.insert(tk.END, html_text[last_end:])
        self._question_text.tag_config('highlight', foreground='red')
        self._question_text.config(state='disabled')  # Disable the Text widget after inserting text

    def check_answer(self, transcript):
        score, redacted_answer_in_html = score_sentence(self.current_sentence, transcript)
        score = np.round(score, 2)
        self.accuracy_score += score
        self.accuracy_score = np.round(self.accuracy_score, 2)
        self._accuracy_score_label['text'] += f" + {score}"

        time_score = calc_time_penalty(self.time_taken, self.current_sentence)
        time_score = np.round(time_score, 2)
        self.time_score += time_score
        self._time_score_label['text'] += f" + {time_score}"

        if score == 1.0 and time_score == 1.0:
            self.correct += 1
            self._correct_label['text'] += f" + 1"
        else:
            self.incorrect += 1
            self._incorrect_label['text'] += f" + 1"
        self.total_questions += 1
        self._total_questions_label['text'] += f" + 1"

        self._scoring_server.set_sentence_score(self.current_sentence, score)
        self._question_text.delete('1.0', tk.END)  # Clear the existing text
        self.insert_colored_text(redacted_answer_in_html)

    def next_question(self, event=None):
        if self.rerolled < 1:  # 1 is max rerolls
            self.current_sentence = self._scoring_server.get_sentence()
            if self._user_answer is not None:
                self._user_answer.destroy()
            self.insert_colored_text(self.current_sentence)
            self.time_start = time.time()

            self._accuracy_score_label['text'] = f"Accuracy score: {self.accuracy_score}"
            self._time_score_label['text'] = f"Time score: {self.time_score}"
            self._correct_label['text'] = f"Correct: {self.correct}"
            self._incorrect_label['text'] = f"Incorrect: {self.incorrect}"
            self._total_questions_label['text'] = f"Total questions: {self.total_questions}"

            self.answered = False
            self.rerolled += 1
            self._record_button['state'] = 'normal'
            self._next_question_button['state'] = 'disabled'


def main():
    app = CzytanieApp()
    app._window.mainloop()


if __name__ == "__main__":
    main()
