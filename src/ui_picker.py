import setting as st

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import CompleteStyle


def _truncate(s: str, n: int) -> str:
    if n <= 0:
        return ""
    if s is None:
        return ""
    s = str(s)
    return s if len(s) <= n else s[: max(0, n - 1)] + "…"


def _fuzzy_in_order(needle: str, haystack: str) -> bool:
    needle = (needle or "").lower()
    haystack = (haystack or "").lower()
    if needle == "":
        return True

    it = iter(haystack)
    for ch in needle:
        for h in it:
            if h == ch:
                break
        else:
            return False
    return True


class SimpleCompleter(Completer):
    def __init__(self, choices, min_chars=0, empty_limit=st.BRANCHES_EMPTY_LIMIT, fuzzy=False, meta_max=0):
        self.choices = list(choices)
        self.min_chars = int(min_chars)
        self.empty_limit = int(empty_limit)
        self.fuzzy = bool(fuzzy)
        self.meta_max = int(meta_max)

    def get_completions(self, document: Document, complete_event):
        text = document.text.strip()

        if text == "":
            if self.min_chars > 0:
                return
            subset = self.choices[: self.empty_limit]
            for value, label, meta in subset:
                meta_out = _truncate(meta, self.meta_max) if self.meta_max > 0 else meta
                yield Completion(
                    text=value,
                    start_position=0,
                    display=label,
                    display_meta=meta_out,
                )
            return

        if len(text) < self.min_chars:
            return

        q = text.lower()
        for value, label, meta in self.choices:
            hay = (str(value) + " " + str(label) + " " + str(meta)).lower()

            ok = _fuzzy_in_order(q, hay) if self.fuzzy else (q in hay)
            if ok:
                meta_out = _truncate(meta, self.meta_max) if self.meta_max > 0 else meta
                yield Completion(
                    text=value,
                    start_position=-len(document.text),
                    display=label,
                    display_meta=meta_out,
                )


def pick_value(choices, title, min_chars=0, empty_limit=50, fuzzy=False, meta_max=0):
    if not choices:
        return None

    canceled = {"v": False}
    kb = KeyBindings()

    @kb.add("escape")
    def _cancel(event):
        canceled["v"] = True
        event.app.exit(result="")

    session = PromptSession(key_bindings=kb)
    completer = SimpleCompleter(
        choices,
        min_chars=min_chars,
        empty_limit=empty_limit,
        fuzzy=fuzzy,
        meta_max=meta_max,
    )

    v = session.prompt(
        f"{title}> ",
        completer=completer,
        complete_while_typing=True,
        complete_style=CompleteStyle.COLUMN,
    ).strip()

    if canceled["v"]:
        return None
    return v if v else None
