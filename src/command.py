import git_adapter as ga
import ui_picker as ui
import setting as st


def cmd_help(args: list[str] | None = None) -> None:
    print(
        "LazyGit (REPL) commands:\n"
        "  help                         Show this help\n"
        "  quit                         Exit LazyGit\n"
        "  clear                        Clear the screen\n"
        "  remotes                      List remote names\n"
        "  branches                     List local branches\n"
        "  commits [N]                  List latest N commits (default: 10)\n"
        "  fetch                        git fetch --all --prune\n"
        "  status                       git status -sb\n"
        "  checkout [branch]            git checkout <branch> (no arg opens picker)\n"
        "  reset [sha]                  git reset <sha> (no arg opens picker)\n"
        "  push [remote] [branch]       git push <remote name> <branch>\n"
        "  pull [remote] [branch]       git pull <remote name> <branch>\n"
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


def cmd_remotes(args: list[str]) -> None:
    if not ga.is_git_repo():
        print("Not a git repository.")
        return
    names = ga.list_remote_names()
    for name in names:
        print(name)


def cmd_branches(args: list[str]) -> None:
    if not ga.is_git_repo():
        print("Not a git repository.")
        return
    
    local_branches = ga.list_local_branches()
    print("Local branches:")
    for local_branch in local_branches:
        print(local_branch)

    remote_branches = ga.list_remote_branches()
    print("\nRemote branches:")
    for remote_branch in remote_branches:
        print(remote_branch)


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
        target = ui.pick_labeled_branch("checkout")
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
        target = ui.pick_commit()
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


def cmd_status(args: list[str]) -> None:
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
    
    code, out, err = ga.fetch()
    if code != 0:
        print(err)
    elif out.strip():
        print(out)


def cmd_push(args: list[str]) -> None:
    if not ga.is_git_repo():
        print("Not a git repository.")
        return

    if len(args) == 0:
        remote = ui.pick_remote_name("push")
        if remote is None:
            return

        branch = ui.pick_unlabeled_branch("push", remote)
        if branch is None:
            return

    elif len(args) == 2 and args[0].strip() and args[1].strip():
        remote = args[0].strip()
        branch = args[1].strip()

    else:
        print("usage: push <remote> <branch>")
        return

    code, out, err = ga.push(remote, branch)
    if code != 0:
        print(err)
    elif out.strip():
        print(out)


def cmd_pull(args: list[str]) -> None:
    if not ga.is_git_repo():
        print("Not a git repository.")
        return

    if len(args) == 0:
        remote = ui.pick_remote_name("pull")
        if remote is None:
            return

        branch = ui.pick_unlabeled_branch("pull", remote)
        if branch is None:
            return

    elif len(args) == 2 and args[0].strip() and args[1].strip():
        remote = args[0].strip()
        branch = args[1].strip()

    else:
        print("usage: pull <remote> <branch>")
        return

    code, out, err = ga.pull(remote, branch)
    if code != 0:
        print(err)
    elif out.strip():
        print(out)
