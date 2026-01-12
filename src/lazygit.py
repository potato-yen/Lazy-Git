import command as cmd
import git_adapter as ga
import setting as st
import utils as ut

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
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
    "checkout": "git checkout [branch] (picker if no arg)",
    "reset": "git reset [sha] (picker if no arg)",
    "status": "git status -sb",
    "fetch": "git fetch --all --prune",
    "push": "git push <remote> <branch> (picker if no arg)",
    "pull": "git pull <remote> <branch> (picker if no arg)",
}


class Cache:
    def __init__(
            self,
            remote_names_cache=None, remote_names_at=0.0,
            unlabeled_branches_cache=None, unlabeled_branches_at=0.0,
            labeled_branches_cache=None, labeled_branches_at=0.0,
            commits_cache=None, commits_at=0.0,
            local_branches_cache=None, local_branches_at=0.0,
            remote_branches_cache=None, remote_branches_at=0.0,
            ):
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

    def get_cached_remote_names(self, ttl_sec=st.CACHE_TTL_SEC) -> list[str]:
        past_time = time.time() - self.remote_names_at
        if self.remote_names_at == 0.0 or past_time > ttl_sec:
            remote_names = ga.list_remote_names()
            self.remote_names_cache = remote_names
            self.remote_names_at = time.time()
        return self.remote_names_cache

    def get_cached_unlabeled_branches(self, ttl_sec=st.CACHE_TTL_SEC) -> dict[str, list[str]]:
        past_time = time.time() - self.unlabeled_branches_cache_at
        if self.unlabeled_branches_cache_at == 0.0 or past_time > ttl_sec:
            branches = ut.remove_label(ga.list_remote_names(), ga.list_remote_branches(), ga.list_local_branches())
            self.unlabeled_branches_cache = branches
            self.unlabeled_branches_cache_at = time.time()
        return self.unlabeled_branches_cache

    def get_cached_labeled_branches(self, ttl_sec=st.CACHE_TTL_SEC) -> list[str]:
        past_time = time.time() - self.labeled_branches_cache_at
        if self.labeled_branches_cache_at == 0.0 or past_time > ttl_sec:
            branches = ga.list_branches()
            self.labeled_branches_cache = branches
            self.labeled_branches_cache_at = time.time()
        return self.labeled_branches_cache

    def get_cached_commits(self, limit=st.COMMITS_LIMIT, ttl_sec=st.CACHE_TTL_SEC) -> list[tuple[str, str]]:
        past_time = time.time() - self.commits_cache_at
        if self.commits_cache_at == 0.0 or past_time > ttl_sec:
            self.commits_cache = ga.list_commits(limit)
            self.commits_cache_at = time.time()
        return self.commits_cache

    def get_cached_local_branches(self, ttl_sec=st.CACHE_TTL_SEC) -> list[str]:
        past_time = time.time() - self.local_branches_cache_at
        if self.local_branches_cache_at == 0.0 or past_time > ttl_sec:
            self.local_branches_cache = ga.list_local_branches()
            self.local_branches_cache_at = time.time()
        return self.local_branches_cache

    def get_cached_remote_branches(self, ttl_sec=st.CACHE_TTL_SEC) -> list[str]:
        past_time = time.time() - self.remote_branches_cache_at
        if self.remote_branches_cache_at == 0.0 or past_time > ttl_sec:
            self.remote_branches_cache = ga.list_remote_branches()
            self.remote_branches_cache_at = time.time()
        return self.remote_branches_cache


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

            query = document.get_word_before_cursor(WORD=True)
            locals_ = self.cache.get_cached_local_branches()
            remotes = self.cache.get_cached_remote_branches()

            items: list[tuple[str, str, str]] = []
            for b in locals_:
                items.append((b, b, "local"))

            for full in remotes:
                if "/" not in full:
                    continue
                remote, name = full.split("/", 1)
                items.append((full, name, remote))

            if query == "":
                for text_, disp, meta in items[: st.BRANCHES_EMPTY_LIMIT]:
                    yield Completion(text=text_, start_position=0, display=disp, display_meta=meta)
                return

            q = query.lower()
            for text_, disp, meta in items:
                hay = f"{disp} {text_} {meta}"
                if ut._fuzzy_in_order(q, hay):
                    yield Completion(text=text_, start_position=-len(query), display=disp, display_meta=meta)
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
                        display_meta=ut._truncate(subject, st.COMMIT_SUBJECT_MAX),
                    )
                return

            q = query.lower()
            for sha, subject in commits:
                hay = f"{sha} {subject}"
                if ut._fuzzy_in_order(q, hay):
                    yield Completion(
                        text=sha,
                        start_position=-len(query),
                        display=sha,
                        display_meta=ut._truncate(subject, st.COMMIT_SUBJECT_MAX),
                    )
            return

        # push / pull
        if first in ("push", "pull"):
            if not ga.is_git_repo():
                return

            if len(parts) > 3:
                return

            # Case 1: "push " / "pull " -> 補 remote names
            if len(parts) == 1 and stripped.endswith(" "):
                names = self.cache.get_cached_remote_names()
                for n in names[: st.REMOTE_NAMES_EMPTY_LIMIT]:
                    yield Completion(text=n, start_position=0, display=n, display_meta="remote")
                return

            # Case 2: "push ori" -> 正在打 remote
            if len(parts) == 2 and not stripped.endswith(" "):
                query = document.get_word_before_cursor(WORD=True)
                names = self.cache.get_cached_remote_names()

                if query == "":
                    for n in names[: st.REMOTE_NAMES_EMPTY_LIMIT]:
                        yield Completion(text=n, start_position=0, display=n, display_meta="remote")
                    return

                q = query.lower()
                for n in names:
                    if ut._fuzzy_in_order(q, n):
                        yield Completion(text=n, start_position=-len(query), display=n, display_meta="remote")
                return

            # Case 3: "push origin " -> remote 確定
            if len(parts) == 2 and stripped.endswith(" "):
                remote = parts[1]
                by_remote = self.cache.get_cached_unlabeled_branches()
                branches = by_remote.get(remote, [])

                for b in branches[: st.BRANCHES_EMPTY_LIMIT]:
                    yield Completion(text=b, start_position=0, display=b, display_meta=remote)
                return

            # Case 4: "push origin ma"
            if len(parts) == 3:
                remote = parts[1]
                query = document.get_word_before_cursor(WORD=True)

                by_remote = self.cache.get_cached_unlabeled_branches()
                branches = by_remote.get(remote, [])

                if query == "":
                    for b in branches[: st.BRANCHES_EMPTY_LIMIT]:
                        yield Completion(text=b, start_position=0, display=b, display_meta=remote)
                    return

                q = query.lower()
                for b in branches:
                    if ut._fuzzy_in_order(q, b):
                        yield Completion(text=b, start_position=-len(query), display=b, display_meta=remote)
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
