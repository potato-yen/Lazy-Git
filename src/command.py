import git_adapter as ga
import ui_picker as ui
import setting as st


def _truncate(s: str, n: int) -> str:
    if n <= 0:
        return ""
    if s is None:
        return ""
    s = str(s)
    return s if len(s) <= n else s[: max(0, n - 1)] + "…"


def pick_branch() -> str | None:
    branches = ga.list_branches()
    choices = [(b, b, "") for b in branches]
    return ui.pick_value(
        choices,
        "checkout",
        min_chars=0,
        empty_limit=st.BRANCHES_EMPTY_LIMIT,
        fuzzy=True,
        meta_max=0,
    )


def pick_commit(limit: int = st.COMMITS_LIMIT) -> str | None:
    commits = ga.list_commits(limit)
    choices = [(sha, sha, _truncate(subject, st.COMMIT_SUBJECT_MAX)) for sha, subject in commits]

    return ui.pick_value(
        choices,
        "reset",
        min_chars=0,
        empty_limit=st.COMMITS_EMPTY_LIMIT_PICKER,
        fuzzy=True,
        meta_max=st.COMMIT_SUBJECT_MAX,
    )


def cmd_help(args=None) -> None:
    print(
        "LazyGit (REPL) commands:\n"
        "  help                    Show this help\n"
        "  quit                    Exit LazyGit\n"
        "  clear                   Clear the screen\n"
        "  branches                List local branches\n"
        "  commits [N]             List latest N commits (default: 10)\n"
        "  checkout [branch]       git checkout <branch> (no arg opens picker)\n"
        "  reset [sha]             git reset <sha> (no arg opens picker)\n"
        "  status                  git status -sb\n"
        "  fetch                   git fetch --all --prune\n"
        "\n"
        "Notes:\n"
        "  - Empty input is ignored.\n"
        "  - Unknown command prints a hint to use 'help'.\n"
        "  - If not in a git repository, git-related commands will print: Not a git repository.\n"
    )


def cmd_clear(args: list[str]) -> None:
    try:
        print("\033[2J\033[H", end="")
    except Exception:
        import os
        os.system("cls" if os.name == "nt" else "clear")


def cmd_branches(args: list[str]) -> None:
    if not ga.is_git_repo():
        print("Not a git repository.")
        return

    for name in ga.list_branches():
        print(name)


def cmd_commits(args: list[str]) -> None:
    if not ga.is_git_repo():
        print("Not a git repository.")
        return

    n = st.COMMITS_PRINT_DEFAULT
    if len(args) >= 1:
        try:
            n = int(args[0])
            if n <= 0:
                raise ValueError
        except ValueError:
            print("usage: commits [N]")
            return

    for sha, subject in ga.list_commits(n):
        print(f"{sha} {subject}")


def cmd_checkout(args: list[str]) -> None:
    if not ga.is_git_repo():
        print("Not a git repository.")
        return

    if len(args) == 0:
        target = pick_branch()
        if target is None:
            return
    elif len(args) == 1 and args[0].strip():
        target = args[0].strip()
    else:
        print("usage: checkout [branch]")
        return

    code, out, err = ga.checkout(target)
    if code != 0:
        print(err)
    elif out.strip():
        print(out)


def cmd_reset(args: list[str]) -> None:
    if not ga.is_git_repo():
        print("Not a git repository.")
        return

    if len(args) == 0:
        target = pick_commit()
        if target is None:
            return
    elif len(args) == 1 and args[0].strip():
        target = args[0].strip()
    else:
        print("usage: reset [sha]")
        return

    code, out, err = ga.reset(target)
    if code != 0:
        print(err)
    elif out.strip():
        print(out)


def cmd_status(args: list[str]) ->None:
    if not ga.is_git_repo():
        print("Not a git repository.")
        return
    
    code, out, err = ga.status()
    if code != 0:
        print(err)
    elif out.strip():
        print(out)


def cmd_fetch(args: list[str]) -> None:
    if not ga.is_git_repo():
        print("Not a git repository.")
        return
    
    code, err = ga.fetch()
    if code != 0:
        print(err)
    else:
        print("Complete.")