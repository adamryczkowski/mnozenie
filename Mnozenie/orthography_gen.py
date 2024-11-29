from openai import OpenAI
import os
from pathlib import Path
import random


def system_prompt() -> str:
    system_prompt = """You are a Polish language teacher that is doing a dictation exercise for his pupils aged 7-8 years. All what you say is grammatically correct Polish."""
    return system_prompt


def make_prompt_template(words_to_include: list[str], n: int) -> str:
    user_prompt = f"""Provide a sample numbered list of 1..{n} one-sentence dictation exercises that includes the following words. If possible, please retain the grammatical form of these words. Write only the words that are going to be dictated.\n:
    {', '.join(words_to_include)}
    """
    return user_prompt


def choose_best_dictation_template(dictation_list: list[str]) -> str:
    user_prompt = """You are given a list of dictation exercises. Choose the one that is the most appropriate, interesting. funny, and grammatically correct. Output in the form "n", where n is the number of the chosen dictation exercise.\n"""
    assert len(dictation_list) > 0
    for i, dictation in enumerate(dictation_list):
        user_prompt += f"{i + 1}. {dictation}\n"

    return user_prompt


def call_the_openai_api(
    system_prompt: str,
    user_prompt: str,
    server_ip: str = "192.168.42.5",
    server_port: int = 1234,
):
    """Calls the local LLM server that is running the OpenAI API. No key is necessary."""

    # Chat with an intelligent assistant in your terminal

    # Point to the local server
    client = OpenAI(
        base_url=f"http://{server_ip}:{server_port}/v1", api_key="lm-studio"
    )

    history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    completion = client.chat.completions.create(
        model="model-identifier",
        messages=history,
        temperature=0.2,
        stream=True,
    )

    new_message = {"role": "assistant", "content": ""}

    for chunk in completion:
        if chunk.choices[0].delta.content:
            # print(chunk.choices[0].delta.content, end="", flush=True)
            new_message["content"] += chunk.choices[0].delta.content

    return new_message["content"]


def make_random_sample_of_dictation_words(n: int) -> list[str]:
    template_file = Path(os.path.dirname(__file__)) / "dictation_words.txt"
    with open(template_file, "r") as f:
        words = f.read()

    words = words.split("\n")

    return random.sample(words, n)


def make_dictation_list_candidates(words: list[str], n: int) -> list[str]:
    user_prompt = make_prompt_template(words, n)
    system_prompt_str = system_prompt()

    dictation_txt = call_the_openai_api(system_prompt_str, user_prompt)

    dictation_list: list[str] = []
    # Parsing the dictation list. It is a numbered list.
    for i, line in enumerate(dictation_txt.split("\n")):
        expected_prefix = f"{i + 1}."
        line = line.strip()
        if line.startswith(expected_prefix):
            dictation_list.append(line[len(expected_prefix) :].strip())
        else:
            raise ValueError(
                f"Error in parsing the dictation list. Expected prefix: {expected_prefix}, got: {line}"
            )

    return dictation_list


def extract_integers_from_str(text: str) -> list[int]:
    """Extracts all the integers from the text"""
    ans = []
    cur_number = ""
    for c in text:
        if c.isdigit():
            cur_number += c
        else:
            if cur_number:
                ans.append(int(cur_number))
                cur_number = ""
    if cur_number:
        ans.append(int(cur_number))
        cur_number = ""
    return ans


def choose_best_dictation(dictation_list: list[str]) -> str:
    user_prompt = choose_best_dictation_template(dictation_list)

    system_prompt_str = system_prompt()

    best_choice_txt: str = call_the_openai_api(system_prompt_str, user_prompt)
    numbers = extract_integers_from_str(best_choice_txt)
    if len(numbers) != 1:
        raise ValueError(f"Expected one number, got {len(numbers)}")

    best_choice = numbers[0]

    return dictation_list[int(best_choice) - 1]


def prepare_dictation_sentence(words: list[str]) -> str:
    dictation_list = make_dictation_list_candidates(words, 5)

    best_one = choose_best_dictation(dictation_list)

    print(", ".join(words))
    print(dictation_list[int(input(best_one)) - 1])
    return best_one


def test():
    words = make_random_sample_of_dictation_words(8)

    stentence = prepare_dictation_sentence(words)
    print(stentence)


if __name__ == "__main__":
    test()
