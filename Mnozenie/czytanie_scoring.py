import difflib


def just_letters(s: str, no_spaces:bool=False) -> str:
    if no_spaces:
        return s.lower().translate(str.maketrans("", "", "!?.,;:- \""))

    return " ".join(s.lower().translate(str.maketrans("", "", "!?.,;:-\"")).split())

class WordIterator:
    _word_boundaries: list[int] # Word boundaries
    _current_word: int
    _sentence:str
    _is_correct: list[bool] # True for all the words that were read correctly.
    def __init__(self, correct_sentence:list[str]):
        """Cares only about the letters without spaces.
        correct_sentence is a vector of words
        """
        # word_boundaries is a running sum of the lengths of the words.
        sum_so_far = 0
        self._word_boundaries = []
        for i in range(0, len(correct_sentence)):
            self._word_boundaries.append(sum_so_far)
            sum_so_far += len(correct_sentence[i])

        self._word_boundaries.append(sum_so_far)

        self._sentence = " ".join(correct_sentence)
        self._current_word = 0
        self._is_correct = [True] * len(correct_sentence)

    def __len__(self)->int:
        return len(self._word_boundaries) - 1

    def __iter__(self):
        return self

    @property
    def current_word(self)->tuple[int,int]:
        left = self._word_boundaries[self._current_word]
        right = self._word_boundaries[self._current_word + 1]
        return left, right

    def __next__(self)->tuple[int,int]:
        if self.EOI:
            raise StopIteration
        self._current_word += 1
        if self.EOI:
            raise StopIteration
        return self.current_word

    @property
    def EOI(self)->bool:
        return self._current_word == len(self)

    def advance_to(self, start_from:int):
        """Advances iteration to the word that contains "start_from" character"""
        if self.EOI:
            return
        left, right = self.current_word
        while not self.EOI:
            if start_from < right:
                return
            try:
                left, right = next(self)
            except StopIteration:
                return
        return

    def mark_rest_of_the_words_incorrect(self):
        self.mark_words_incorrect(len(self._sentence))
    def mark_words_incorrect(self,  end_to: int):
        """Marks all the words up until end_to (including end_to) as incorrect.
        Sets the iteration on the next item after the last word set as incorrect.
        """
        if self.EOI:
            return
        left, right = self.current_word
        while not self.EOI:
            if left >= end_to:
                return

            self._is_correct[self._current_word] = False
            try:
                left, right = next(self)
            except StopIteration:
                return

    @property
    def last_character_position(self)->int:
        return self._word_boundaries[-1]


    def correct_words(self)->list[bool]:
        return self._is_correct

    def __str__(self):
        """
        Prints the sentence with two markers "^" that indicate the current positions.
        """
        left, right = self.current_word
        left += self._current_word
        right += self._current_word
        row1 = self._sentence + "\n"
        row2 = f"{' ' * left}^{' ' * (right - left - 1)}^\n"
        return row1 + row2

    def __repr__(self):
        return self.__str__()

def score_sentence(correct_sentence:str, user_sentence: str) -> tuple[float, str]:
    words = WordIterator(just_letters(correct_sentence).split())

    print(str(words))


    sequence_matcher = difflib.SequenceMatcher(None, just_letters(correct_sentence, True), just_letters(user_sentence, True))
    correct_sentence = just_letters(correct_sentence, True)
    user_sentence = just_letters(user_sentence, True)

    row_1 = just_letters(correct_sentence) + "\n"
    row_2 = ""
    mb = sequence_matcher.get_matching_blocks()
    mb = [mb for mb in mb if mb.size > 0]
    for i, b in enumerate(mb):
        row_2 += f"{' ' * (b.a - len(row_2))}{str(i) * b.size}"
    print(row_1 + row_2)

    if len(mb) == 0:
        return 0, highlight_sentence(correct_sentence, words.correct_words())

    i = 0
    while i < len(mb):
        match = mb[i]
        words.mark_words_incorrect(match.a)
        words.advance_to(match.a + match.size)
        i+=1

    words.mark_rest_of_the_words_incorrect()

    total_word_count = len(words.correct_words())
    wrong_words = sum(1 for word in words.correct_words() if not word)

    return (total_word_count - wrong_words) / total_word_count, highlight_sentence(correct_sentence, words.correct_words())


def highlight_sentence(correct_sentence:str, words:list[bool])->str:
    reference_tokens = correct_sentence.split()
    formatted_text = ""
    for i, token in enumerate(reference_tokens):
        if words[i]:
            formatted_text += token + " "
        else:
            formatted_text += f"<span style='background-color: #FF0000'>{token}</span> "
    return formatted_text