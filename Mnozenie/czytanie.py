import heapq
import tkinter as tk
from dataclasses import dataclass, field
import numpy as np

import whisper

from sound_recorder import SoundRecorder

class Speech2Text:
    _model: whisper.model

    def __init__(self):
        self._model = whisper.load_model("medium")

    def get_transcript(self, sound) -> str:
        return self._model.transcribe(sound)['text']


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



def calculate_timeout_from_sentence(sentence: str) -> float:
    return len(just_letters(sentence)) / 3 + 4


class CzytanieApp:
    _window: tk.Tk
    _sound_recorder: SoundRecorder
    _scoring_server: ScoringServer
    _speech2text: Speech2Text
    _question_text: tk.Text
    _record_button: tk.Button
    _next_question_button: tk.Button
    _score_label: tk.Label
    def __init__(self):
        self._window = tk.Tk()
        self._window.title("Czytanie")

        self._window.configure(bg='black')

        self._sound_recorder = SoundRecorder()
        self._scoring_server = ScoringServer()
        self._speech2text = Speech2Text()

        self._question_text = tk.Text(self._window, height=1, borderwidth=0, background='black', foreground='white')
        self._question_text.pack()

        self._record_button = tk.Button(self._window, text="Record", background='black', foreground='white')
        self._record_button.pack()
        self._record_button.bind("<ButtonPress>", self.start_recording)
        self._record_button.bind("<ButtonRelease>", self.stop_recording)

        self._next_question_button = tk.Button(self._window, text="Next question", background='black', foreground='white')
        self._next_question_button.pack()
        self._next_question_button.bind("<ButtonPress>", self.next_question)

        self._score_label = tk.Label(self._window, text="Score: 0", background='black', foreground='white')
        self._score_label.pack()

        self.next_question()

    def start_recording(self, event):
        self._sound_recorder.start_recording()

    def stop_recording(self, event):
        self._sound_recorder.stop_recording()
        sound = self._sound_recorder.get_last_recording_as_whisper_sound()
        self._sound_recorder.play_last_recording()
        transcript = self._speech2text.get_transcript(sound).strip()
        if transcript == "":
            return
        self._user_answer = tk.Text(self._window, height=1, borderwidth=0, background='black', foreground='white')
        self._user_answer.pack()
        self._user_answer.insert(tk.END, transcript)

        self.check_answer(transcript)
        self._record_button['state'] = 'disabled'
        self._next_question_button['state'] = 'normal'

    def insert_colored_text(self, html_text):
        import re
        pattern = re.compile(r"<span style='background-color: #FF0000'>(.*?)</span>")
        last_end = 0
        self._question_text.config(state='normal')  # Enable the Text widget before inserting text
        self._question_text.delete('1.0', tk.END)  # Clear the existing text
        for match in pattern.finditer(html_text):
            self._question_text.insert(tk.END, html_text[last_end:match.start()])
            self._question_text.insert(tk.END, match.group(1), 'highlight')
            last_end = match.end()
        self._question_text.insert(tk.END, html_text[last_end:])
        self._question_text.tag_config('highlight', foreground='red')
        self._question_text.config(state='disabled')  # Disable the Text widget after inserting text

    def check_answer(self, transcript):
        score, redacted_answer_in_html = score_sentence(self.current_sentence, transcript)
        self._scoring_server.set_sentence_score(self.current_sentence, score)
        self._question_text.delete('1.0', tk.END)  # Clear the existing text
        self.insert_colored_text(redacted_answer_in_html)
        self.update_score()

    def update_score(self):
        total_score = sum(sentence.score for sentence in self._scoring_server._scores.values())
        self._score_label['text'] = f"Score: {total_score}"

    def next_question(self, event=None):
        self.current_sentence = self._scoring_server.get_sentence()
        self.insert_colored_text(self.current_sentence)
        self._next_question_button['state'] = 'disabled'
        self._record_button['state'] = 'normal'  # Enable the record button

def main():

    app = CzytanieApp()
    app._window.mainloop()


if __name__ == "__main__":
    main()
