import git_adapter as ga

def cmd_help(args=None) -> None:
    print(
        "LazyGit (REPL) commands:\n"
        "  help                    Show this help\n"
        "  exit | quit             Exit LazyGit\n"
        "  clear                   Clear the screen\n"
        "  branches                List local branches\n"
        "  commits [N]             List latest N commits (default: 10)\n"
        "  checkout <branch>       git checkout <branch>\n"
        "  reset <sha>             git reset <sha>\n"
        "\n"
        "Notes:\n"
        "  - Empty input is ignored.\n"
        "  - Unknown command prints a hint to use 'help'.\n"
        "  - If not in a git repository, git-related commands will print: Not a git repository.\n"
    )
def cmd_clear(args: list[str]) -> None:
    try:
        # ANSI: 清螢幕(2J) + 游標移到左上(H)
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

    n = 10
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
    if len(args) != 1 or not args[0].strip():
        print("usage: checkout <branch>")
        return

    code, out, err = ga.checkout(args[0])
    if code != 0:
        print(err)
    elif out.strip():
        print(out)

def cmd_reset(args: list[str]) -> None:
    if not ga.is_git_repo():
        print("Not a git repository.")
        return
    if len(args) != 1 or not args[0].strip():
        print("usage: reset <sha>")
        return

    code, out, err = ga.reset(args[0])
    if code != 0:
        print(err)
    elif out.strip():
        print(out)