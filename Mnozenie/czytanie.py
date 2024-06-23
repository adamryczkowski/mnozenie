import heapq
import tkinter as tk
from dataclasses import dataclass, field
import numpy as np
import difflib

import whisper

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


def just_letters(s: str) -> str:
    return " ".join(s.lower().translate(str.maketrans("", "", "!?.,;:-")).split())


def calculate_timeout_from_sentence(sentence: str) -> float:
    return len(just_letters(sentence)) / 3 + 4


def score_sentence(correct_sentence: str, user_sentence: str) -> tuple[float, str]:
    sequence_matcher = difflib.SequenceMatcher(None, just_letters(correct_sentence), just_letters(user_sentence))
    # Calculate number of words that were read wrong.
    # 1. Calculate positions of spaces in the correct sentence
    correct_spaces = [0] + [i for i, c in enumerate(correct_sentence) if c == " "]
    correct_spaces.append(len(correct_sentence))
    # Find what words were read wrong
    wrong_words = 0
    mb = sequence_matcher.get_matching_blocks()
    mb = [mb for mb in mb if mb.size > 0]

    left_word_pos_idx = 0
    sequence_pos = 0
    words = [True] * (len(correct_spaces) - 1)  # Each word will get a True if was correctly read, or False if not

    while True:  # Driven by correct_pos.
        correct_pos_left = mb[sequence_pos].a
        correct_pos_right = mb[sequence_pos].size

        while True:
            left_word_pos = correct_spaces[left_word_pos_idx]
            right_word_pos = correct_spaces[left_word_pos_idx + 1]
            if right_word_pos < correct_pos_right:
                left_word_pos_idx += 1
                if left_word_pos_idx == len(correct_spaces) - 1:
                    break
                continue
            break
        if left_word_pos_idx == len(correct_spaces) - 1:
            break

        sequence_pos += 1
        if sequence_pos == len(mb):
            break
        correct_pos_left = mb[sequence_pos].a
        correct_pos_right = mb[sequence_pos].size + mb[sequence_pos].a
        while left_word_pos < correct_pos_left:
            words[left_word_pos_idx] = False
            left_word_pos_idx += 1
            if left_word_pos_idx == len(correct_spaces) - 1:
                break
            left_word_pos = correct_spaces[left_word_pos_idx]
            right_word_pos = correct_spaces[left_word_pos_idx + 1]
        if left_word_pos_idx == len(correct_spaces) - 1:
            break

    total_word_count = len(correct_spaces) - 1
    wrong_words = sum(1 for word in words if not word)

    reference_tokens = correct_sentence.split()
    formatted_text = ""
    for i, token in enumerate(reference_tokens):
        if words[i]:
            formatted_text += token + " "
        else:
            formatted_text += f"<span style='background-color: #FF0000'>{token}</span> "

    return (total_word_count - wrong_words) / total_word_count, formatted_text


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

        self.answered = False
        self.rerolled = 0

        self._window.configure(bg='black')

        self._user_answer = None

        self._sound_recorder = SoundRecorder()
        self._scoring_server = ScoringServer()
        self._speech2text = Speech2Text()

        # self.loading_frames = [tk.PhotoImage(file='loading.gif',format = 'gif -index %i' %(i)) for i in range(17)]

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

        self._score_label = tk.Label(self._window, text="Score: 0", background='black', foreground='white')
        self._score_label.pack()

        self.next_question()

    def start_recording(self, event):
        if self.answered == False:
            self._sound_recorder.start_recording()

    # def update_loading_circle(self):
    #     self._loading_circle_label.configure(image=self.loading_frames[self.loading_frame])
    #     self.loading_frame += 1
    #     if self.loading_frame == 17:
    #         self.loading_frame = 0
    #     self._window.after(100, self.update_loading_circle)

    def stop_recording(self, event):
        self._sound_recorder.stop_recording()
        # self.loading_frame = 0
        # self._loading_circle_label = tk.Label(self._window)
        # self._loading_circle_label.pack()
        # self._window.after(0, self.update_loading_circle)

        sound = self._sound_recorder.get_last_recording_as_whisper_sound()
        self._sound_recorder.play_last_recording()
        transcript = self._speech2text.get_transcript(sound)
        # self._loading_circle_label.destroy()
        if transcript == "":
            return
        self.answered = True
        self.rerolled = 0
        self._user_answer = tk.Text(self._window, height=1, background='black', foreground='white')
        self._user_answer.delete('1.0', tk.END)
        self._user_answer.insert(tk.END, transcript)
        self._user_answer.pack()

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
        if self.rerolled < 1:  # 1 is max rerolls
            self.rerolled += 1
            self.current_sentence = self._scoring_server.get_sentence()
            self.answered = False
            if self._user_answer is not None:
                self._user_answer.destroy()
            self.insert_colored_text(self.current_sentence)
            self._next_question_button['state'] = 'disabled'
            self._record_button['state'] = 'normal'  # Enable the record button


def main():
    # print(score_sentence("123 abcdefghijklm 12", "123 aXbcdeXghijkXm 12"))
    # print(score_sentence("123 abcdefghijklm 12", "123 Xabcdefghijklm 12"))
    # print(score_sentence("123 abcdefghijklm 12", "123X Xabcdefghijklm 12"))
    # print(score_sentence("123 abcdefghijklm 12", "123 XabcdefghijklmX 12"))
    # print(score_sentence("123 abcdefghijklm 12", "123 XabcdefghijklmX X12"))
    # print(score_sentence("123 abcdefgh 12 abcd 987654 ABCDEFGHIJ xyz", "123 abcdXefgh 12 abcd987654 ABCDEFGHIJ xyz"))
    # print(score_sentence("123 abcdefgh 12 1234", "123 abcXXXX 1234"))
    # print(score_sentence("123 1234567 12 1234", "123 1234567 12 1234"))
    #
    # print(score_sentence("Ala ma kota", "Ala ma psa"))
    # print(score_sentence('Człowiek jest silniejszy, kiedy stawia czoła wyzwaniom. To odwaga napędza nas do działania.', 'Człowiek jest silniejszy, kiedy stawia czoła wyzwaniom do odwagi napędza nas do działania.'))

    app = CzytanieApp()
    app._window.mainloop()


if __name__ == "__main__":
    main()
