import difflib


def just_letters(s: str) -> str:
    return " ".join(s.lower().translate(str.maketrans("", "", "!?.,;:-–…")).split())


def calculate_timeout_from_sentence(sentence: str) -> float:
    return len(just_letters(sentence)) / 1.5 + 6


def calc_time_penalty(time_taken, sentence: str) -> float:
    timeout = calculate_timeout_from_sentence(sentence)

    if time_taken < timeout * 2 and not time_taken < timeout:
        return 0.5
    if time_taken < timeout:
        return 1
    return 0


def score_sentence(correct_sentence: str, user_sentence: str) -> tuple[float, str]:
    sequence_matcher = difflib.SequenceMatcher(
        None, just_letters(correct_sentence), just_letters(user_sentence)
    )
    # Calculate number of words that were read wrong.
    # 1. Calculate positions of spaces in the correct sentence
    correct_spaces = [-1] + [i for i, c in enumerate(correct_sentence) if c == " "]
    correct_spaces.append(len(correct_sentence))
    # Find what words were read wrong
    wrong_words = 0
    mb = sequence_matcher.get_matching_blocks()
    mb = [mb for mb in mb if mb.size > 0]
    if len(mb) == 0:
        return 0, highlight_sentence(
            correct_sentence, [False] * (len(correct_spaces) - 1)
        )

    left_word_pos_idx = 0
    sequence_pos = 0
    words = [True] * (
        len(correct_spaces) - 1
    )  # Each word will get a True if was correctly read, or False if not

    correct_pos_left = mb[sequence_pos].a
    correct_pos_right = mb[sequence_pos].size
    # All the words before the first match are wrong.
    while correct_spaces[left_word_pos_idx] + 1 < correct_pos_left:
        words[left_word_pos_idx] = False
        left_word_pos_idx += 1
        if left_word_pos_idx == len(correct_spaces) - 1:
            return 0, highlight_sentence(correct_sentence, words)

    while True:  # Driven by correct_pos.
        correct_pos_left = mb[sequence_pos].a
        correct_pos_right = mb[sequence_pos].size + mb[sequence_pos].a

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
            # We are going to exit. All the words not read are wrong (missing).
            left_word_pos_idx += 1
            while left_word_pos_idx < len(correct_spaces) - 1:
                words[left_word_pos_idx] = False
                left_word_pos_idx += 1
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

    return (total_word_count - wrong_words) / total_word_count, highlight_sentence(
        correct_sentence, words
    )


def highlight_sentence(correct_sentence: str, words: list[bool]) -> str:
    reference_tokens = correct_sentence.split()
    formatted_text = ""
    for i, token in enumerate(reference_tokens):
        if words[i]:
            formatted_text += token + " "
        else:
            formatted_text += f"<span style='background-color: #FF0000'>{token}</span> "
    return formatted_text
