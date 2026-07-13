import re
from dataclasses import dataclass
from difflib import SequenceMatcher


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower().replace("’", "'"))


@dataclass(frozen=True)
class DialogueComparison:
    ok: bool
    expected: list[str]
    actual: list[str]
    missing: list[str]
    unexpected: list[str]


def compare_dialogue(expected_text: str, actual_text: str) -> DialogueComparison:
    expected = words(expected_text)
    actual = words(actual_text)
    missing: list[str] = []
    unexpected: list[str] = []
    for tag, expected_start, expected_end, actual_start, actual_end in SequenceMatcher(
        a=expected, b=actual, autojunk=False
    ).get_opcodes():
        if tag in {"delete", "replace"}:
            missing.extend(expected[expected_start:expected_end])
        if tag in {"insert", "replace"}:
            unexpected.extend(actual[actual_start:actual_end])
    return DialogueComparison(not missing and not unexpected, expected, actual, missing, unexpected)
