from typing import Callable, Iterable

import command as cmd
import git_adapter as ga
import setting as st
import utils as ut

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.shortcuts import CompleteStyle

import time


_COMMAND_META = {
    "help": "Show help",
    "quit": "Exit LazyGit",
    "clear": "Clear the screen",
    "remotes": "List remote names",
    "branches": "List all branches",
    "commits": "List commits (commits [N])",
    "new": "git branch <branch>",
    "checkout": "git checkout [branch] (picker if no arg)",
    "reset": "git reset [sha] (picker if no arg)",
    "status": "git status -sb",
    "fetch": "git fetch --all --prune",
    "push": "git push <remote> <branch> (picker if no arg)",
    "pull": "git pull <remote> <branch> (picker if no arg)",
}


def _yield_items(
    *,
    items: list[tuple[str, str, str]],  # (text, display, meta)
    query: str,
    empty_limit: int,
    fuzzy_fn: Callable[[str, str], bool],
) -> Iterable[Completion]:
    if query == "":
        for text, disp, meta in items[:empty_limit]:
            yield Completion(text=text, start_position=0, display=disp, display_meta=meta)
        return

    q = query.lower()
    for text, disp, meta in items:
        hay = f"{disp} {text} {meta}"
        if fuzzy_fn(q, hay):
            yield Completion(text=text, start_position=-len(query), display=disp, display_meta=meta)


def _arg_index(parts: list[str], stripped: str) -> int:
    if len(parts) <= 1:
        return 0
    return (len(parts) - 1) if stripped.endswith(" ") else (len(parts) - 2)


class Cache:
    def __init__(
        self,
        remote_names_cache: list[str] | None = None,
        remote_names_at: float = 0.0,
        unlabeled_branches_cache: dict[str, list[str]] | None = None,
        unlabeled_branches_at: float = 0.0,
        labeled_branches_cache: list[str] | None = None,
        labeled_branches_at: float = 0.0,
        commits_cache: list[tuple[str, str]] | None = None,
        commits_at: float = 0.0,
        local_branches_cache: list[str] | None = None,
        local_branches_at: float = 0.0,
        remote_branches_cache: list[str] | None = None,
        remote_branches_at: float = 0.0,
    ) -> None:
        self.remote_names_cache = remote_names_cache if remote_names_cache is not None else []
        self.unlabeled_branches_cache = unlabeled_branches_cache if unlabeled_branches_cache is not None else {}
        self.labeled_branches_cache = labeled_branches_cache if labeled_branches_cache is not None else []
        self.commits_cache = commits_cache if commits_cache is not None else []
        self.local_branches_cache = local_branches_cache if local_branches_cache is not None else []
        self.remote_branches_cache = remote_branches_cache if remote_branches_cache is not None else []

        self.remote_names_at = float(remote_names_at)
        self.unlabeled_branches_cache_at = float(unlabeled_branches_at)
        self.labeled_branches_cache_at = float(labeled_branches_at)
        self.commits_cache_at = float(commits_at)
        self.local_branches_cache_at = float(local_branches_at)
        self.remote_branches_cache_at = float(remote_branches_at)

    def get_cached_remote_names(self, ttl_sec: float = st.CACHE_TTL_SEC) -> list[str]:
        past_time = time.time() - self.remote_names_at
        if self.remote_names_at == 0.0 or past_time > ttl_sec:
            self.remote_names_cache = ga.list_remote_names()
            self.remote_names_at = time.time()
        return self.remote_names_cache

    def get_cached_unlabeled_branches(self, ttl_sec: float = st.CACHE_TTL_SEC) -> dict[str, list[str]]:
        past_time = time.time() - self.unlabeled_branches_cache_at
        if self.unlabeled_branches_cache_at == 0.0 or past_time > ttl_sec:
            branches = ut.remove_label(ga.list_remote_names(), ga.list_remote_branches(), ga.list_local_branches())
            self.unlabeled_branches_cache = branches
            self.unlabeled_branches_cache_at = time.time()
        return self.unlabeled_branches_cache

    def get_cached_labeled_branches(self, ttl_sec: float = st.CACHE_TTL_SEC) -> list[str]:
        past_time = time.time() - self.labeled_branches_cache_at
        if self.labeled_branches_cache_at == 0.0 or past_time > ttl_sec:
            self.labeled_branches_cache = ga.list_branches()
            self.labeled_branches_cache_at = time.time()
        return self.labeled_branches_cache

    def get_cached_commits(
        self,
        limit: int = st.COMMITS_LIMIT,
        ttl_sec: float = st.CACHE_TTL_SEC,
    ) -> list[tuple[str, str]]:
        past_time = time.time() - self.commits_cache_at
        if self.commits_cache_at == 0.0 or past_time > ttl_sec:
            self.commits_cache = ga.list_commits(limit)
            self.commits_cache_at = time.time()
        return self.commits_cache

    def get_cached_local_branches(self, ttl_sec: float = st.CACHE_TTL_SEC) -> list[str]:
        past_time = time.time() - self.local_branches_cache_at
        if self.local_branches_cache_at == 0.0 or past_time > ttl_sec:
            self.local_branches_cache = ga.list_local_branches()
            self.local_branches_cache_at = time.time()
        return self.local_branches_cache

    def get_cached_remote_branches(self, ttl_sec: float = st.CACHE_TTL_SEC) -> list[str]:
        past_time = time.time() - self.remote_branches_cache_at
        if self.remote_branches_cache_at == 0.0 or past_time > ttl_sec:
            self.remote_branches_cache = ga.list_remote_branches()
            self.remote_branches_cache_at = time.time()
        return self.remote_branches_cache


class LazyGitCompleter(Completer):
    def __init__(self, cache: Cache) -> None:
        self.cache = cache

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        text = document.text_before_cursor
        stripped = text.lstrip()

        if stripped == "":
            for name, meta in _COMMAND_META.items():
                yield Completion(text=name, start_position=0, display=name, display_meta=meta)
            return

        parts = stripped.split()
        first = parts[0]

        # command completion
        if len(parts) == 1 and not stripped.endswith(" "):
            word = parts[0]
            for name, meta in _COMMAND_META.items():
                if name.startswith(word):
                    yield Completion(text=name, start_position=-len(word), display=name, display_meta=meta)
            return

        # checkout:
        if first == "checkout":
            if not ga.is_git_repo():
                return

            query = document.get_word_before_cursor(WORD=True)
            locals_ = self.cache.get_cached_local_branches()
            remotes = self.cache.get_cached_remote_branches()

            items: list[tuple[str, str, str]] = [(b, b, "local") for b in locals_]
            for full in remotes:
                if "/" not in full:
                    continue
                remote, name = full.split("/", 1)
                items.append((full, name, remote))

            yield from _yield_items(
                items=items,
                query=query,
                empty_limit=st.BRANCHES_EMPTY_LIMIT,
                fuzzy_fn=ut._fuzzy_in_order,
            )
            return

        # reset
        if first == "reset":
            if not ga.is_git_repo():
                return

            query = document.get_word_before_cursor(WORD=True)
            commits = self.cache.get_cached_commits(st.COMMITS_LIMIT)

            items: list[tuple[str, str, str]] = [
                (sha, sha, ut._truncate(subject, st.COMMIT_SUBJECT_MAX))
                for sha, subject in commits
            ]

            yield from _yield_items(
                items=items,
                query=query,
                empty_limit=st.COMMITS_EMPTY_LIMIT_REPL,
                fuzzy_fn=ut._fuzzy_in_order,
            )
            return

        # push / pull
        if first in ("push", "pull"):
            if not ga.is_git_repo():
                return

            if len(parts) > 3:
                return

            arg_i = _arg_index(parts, stripped)
            query = document.get_word_before_cursor(WORD=True)

            # arg0: remote
            if arg_i == 0:
                names = self.cache.get_cached_remote_names()
                items = [(n, n, "remote") for n in names]
                yield from _yield_items(
                    items=items,
                    query=query,
                    empty_limit=st.REMOTE_NAMES_EMPTY_LIMIT,
                    fuzzy_fn=ut._fuzzy_in_order,
                )
                return

            # arg1: branch (depends on remote)
            if arg_i == 1:
                remote = parts[1] if len(parts) >= 2 else ""
                by_remote = self.cache.get_cached_unlabeled_branches()
                branches = by_remote.get(remote, [])
                items = [(b, b, remote) for b in branches]
                yield from _yield_items(
                    items=items,
                    query=query,
                    empty_limit=st.BRANCHES_EMPTY_LIMIT,
                    fuzzy_fn=ut._fuzzy_in_order,
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
        "remotes": cmd.cmd_remotes,
        "branches": cmd.cmd_branches,
        "commits": cmd.cmd_commits,
        "new": cmd.cmd_new,
        "checkout": cmd.cmd_checkout,
        "reset": cmd.cmd_reset,
        "clear": cmd.cmd_clear,
        "status": cmd.cmd_status,
        "fetch": cmd.cmd_fetch,
        "push": cmd.cmd_push,
        "pull": cmd.cmd_pull,
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
