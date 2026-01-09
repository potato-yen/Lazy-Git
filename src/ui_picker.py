import setting as st

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import CompleteStyle


class SimpleCompleter(Completer):
    def __init__(self, choices, min_chars=0, empty_limit=st.BRANCHES_EMPTY_LIMIT):
        self.choices = list(choices)
        self.min_chars = int(min_chars)
        self.empty_limit = int(empty_limit)

    def get_completions(self, document: Document, complete_event):
        text = document.text.strip()

        if text == "":
            if self.min_chars > 0:
                return
            subset = self.choices[: self.empty_limit]
            for value, label, meta in subset:
                yield Completion(
                    text=value,
                    start_position=0,
                    display=label,
                    display_meta=meta,
                )
            return

        if len(text) < self.min_chars:
            return

        q = text.lower()
        for value, label, meta in self.choices:
            hay = (str(value) + " " + str(label) + " " + str(meta)).lower()
            if q in hay:
                yield Completion(
                    text=value,
                    start_position=-len(document.text),
                    display=label,
                    display_meta=meta,
                )


def pick_value(choices, title, min_chars=0, empty_limit=50):
    """
    choices: [(value, label, meta), ...]
    Enter -> 回 value
    Esc   -> 回 None
    """
    if not choices:
        return None

    canceled = {"v": False}
    kb = KeyBindings()

    @kb.add("escape")
    def _cancel(event):
        canceled["v"] = True
        event.app.exit(result="")

    session = PromptSession(key_bindings=kb)
    completer = SimpleCompleter(choices, min_chars=min_chars, empty_limit=empty_limit)

    v = session.prompt(
        f"{title}> ",
        completer=completer,
        complete_while_typing=True,
        complete_style=CompleteStyle.COLUMN,
    ).strip()

    if canceled["v"]:
        return None
    return v if v else None
