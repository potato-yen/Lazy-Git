import git_adapter as ga
import setting as st
import utils as ut

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import CompleteStyle


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
                meta_out = ut._truncate(meta, self.meta_max) if self.meta_max > 0 else meta
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

            ok = ut._fuzzy_in_order(q, hay) if self.fuzzy else (q in hay)
            if ok:
                meta_out = ut._truncate(meta, self.meta_max) if self.meta_max > 0 else meta
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


def pick_remote_name(mode: str) -> str | None:
    remote_names = ga.list_remote_names()
    choices = [(n, n, "") for n in remote_names]
    return pick_value(
        choices,
        mode,
        min_chars=0,
        empty_limit=st.REMOTE_NAMES_EMPTY_LIMIT,
        fuzzy=True,
        meta_max=0,
    )


def pick_unlabeled_branch(mode: str, remote_name: str) -> str | None:
    categorized = ut.remove_label(ga.list_remote_names(), ga.list_remote_branches(), ga.list_local_branches())
    branches = categorized.get(remote_name)
    if branches is None:
        return 
    
    choices = [(b, b, "") for b in branches]
    return pick_value(
        choices,
        mode,
        min_chars=0,
        empty_limit=st.BRANCHES_EMPTY_LIMIT,
        fuzzy=True,
        meta_max=0,
    )


def pick_labeled_branch(mode: str) -> str | None:
    branches = ga.list_branches()
    choices = [(b, b, "") for b in branches]
    return pick_value(
        choices,
        mode,
        min_chars=0,
        empty_limit=st.BRANCHES_EMPTY_LIMIT,
        fuzzy=True,
        meta_max=0,
    )


def pick_commit(limit: int = st.COMMITS_LIMIT) -> str | None:
    commits = ga.list_commits(limit)
    choices = [(sha, sha, ut._truncate(subject, st.COMMIT_SUBJECT_MAX)) for sha, subject in commits]

    return pick_value(
        choices,
        "reset",
        min_chars=0,
        empty_limit=st.COMMITS_EMPTY_LIMIT_PICKER,
        fuzzy=True,
        meta_max=st.COMMIT_SUBJECT_MAX,
    )
