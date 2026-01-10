import command as cmd
import git_adapter as ga
import setting as st

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.shortcuts import CompleteStyle

import time


_COMMAND_META = {
    "help": "Show help",
    "quit": "Exit LazyGit",
    "clear": "Clear the screen",
    "branches": "List local branches",
    "commits": "List commits (commits [N])",
    "checkout": "git checkout [branch] (picker if no arg)",
    "reset": "git reset [sha] (picker if no arg)",
    "status": "git status -sb",
    "fetch": "git fetch --all --prune"
}


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


class Cache:
    def __init__(self, branches_cache=None, commits_cache=None, branches_at=0.0, commits_at=0.0):
        self.branches_cache = branches_cache if branches_cache is not None else []
        self.commits_cache = commits_cache if commits_cache is not None else []
        self.branches_cache_at = float(branches_at)
        self.commits_cache_at = float(commits_at)

    def get_cached_branches(self, ttl_sec=st.CACHE_TTL_SEC) -> list[str]:
        past_time = time.time() - self.branches_cache_at
        if self.branches_cache_at == 0.0 or past_time > ttl_sec:
            self.branches_cache = ga.list_branches()
            self.branches_cache_at = time.time()
        return self.branches_cache

    def get_cached_commits(self, limit=st.COMMITS_LIMIT, ttl_sec=st.CACHE_TTL_SEC) -> list[tuple[str, str]]:
        past_time = time.time() - self.commits_cache_at
        if self.commits_cache_at == 0.0 or past_time > ttl_sec:
            self.commits_cache = ga.list_commits(limit)
            self.commits_cache_at = time.time()
        return self.commits_cache


class LazyGitCompleter(Completer):
    def __init__(self, cache):
        self.cache = cache

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor
        stripped = text.lstrip()

        if stripped == "":
            for name, meta in _COMMAND_META.items():
                yield Completion(text=name, start_position=0, display=name, display_meta=meta)
            return

        parts = stripped.split()
        first = parts[0]

        # 補全指令
        if len(parts) == 1 and not stripped.endswith(" "):
            word = parts[0]
            for name, meta in _COMMAND_META.items():
                if name.startswith(word):
                    yield Completion(text=name, start_position=-len(word), display=name, display_meta=meta)
            return

        # checkout branch
        if first == "checkout":
            if not ga.is_git_repo():
                return
            branches = self.cache.get_cached_branches()
            query = document.get_word_before_cursor(WORD=True)

            if query == "":
                for b in branches[: st.BRANCHES_EMPTY_LIMIT]:
                    yield Completion(text=b, start_position=0, display=b, display_meta="branch")
                return

            q = query.lower()
            for b in branches:
                if _fuzzy_in_order(q, b):
                    yield Completion(text=b, start_position=-len(query), display=b, display_meta="branch")
            return

        # reset
        if first == "reset":
            if not ga.is_git_repo():
                return

            query = document.get_word_before_cursor(WORD=True)
            commits = self.cache.get_cached_commits(st.COMMITS_LIMIT)

            if query == "":
                for sha, subject in commits[: st.COMMITS_EMPTY_LIMIT_REPL]:
                    yield Completion(
                        text=sha,
                        start_position=0,
                        display=sha,
                        display_meta=_truncate(subject, st.COMMIT_SUBJECT_MAX),
                    )
                return

            q = query.lower()
            for sha, subject in commits:
                hay = f"{sha} {subject}"
                if _fuzzy_in_order(q, hay):
                    yield Completion(
                        text=sha,
                        start_position=-len(query),
                        display=sha,
                        display_meta=_truncate(subject, st.COMMIT_SUBJECT_MAX),
                    )
            return


def dispatch(tokens: list[str]) -> bool:
    if not tokens:
        return True

    name, args = tokens[0], tokens[1:]

    if name == "quit":
        return False

    table = {
        "help": cmd.cmd_help,
        "branches": cmd.cmd_branches,
        "commits": cmd.cmd_commits,
        "checkout": cmd.cmd_checkout,
        "reset": cmd.cmd_reset,
        "clear": cmd.cmd_clear,
        "status": cmd.cmd_status,
        "fetch": cmd.cmd_fetch,
    }

    handler = table.get(name)
    if handler is None:
        print("unknown command. type 'help'")
        return True

    handler(args)
    return True


def parse_line(line: str) -> list[str]:
    return line.strip().split()


def repl_loop() -> int:
    cache = Cache()
    completer = LazyGitCompleter(cache)
    session = PromptSession(
        completer=completer,
        complete_while_typing=True,
        complete_style=CompleteStyle.COLUMN,
    )

    while True:
        try:
            line = session.prompt("lazygit> ")
        except (EOFError, KeyboardInterrupt):
            return 0

        tokens = parse_line(line)
        if dispatch(tokens) is False:
            return 0


if __name__ == "__main__":
    raise SystemExit(repl_loop())