import command as cmd

def dispatch(tokens: list[str]) -> bool:
    if not tokens:
        return True

    name, args = tokens[0], tokens[1:]

    if name in ("quit", "exit"):
        return False

    table = {
        "help": cmd.cmd_help,
        "branches": cmd.cmd_branches,
        "commits": cmd.cmd_commits,
        "checkout": cmd.cmd_checkout,
        "reset": cmd.cmd_reset,
    }

    handler = table.get(name)
    if handler is None:
        print("unknown command. type 'help'")
        return True

    handler(args)
    return True


def parse_lineparse(line : str) -> list[str]:
    return line.strip().split()


def repl_loop() -> int:
    while(True):
        try:
            line = input("LazyGit> ")
        except EOFError:
            return 0
        except KeyboardInterrupt:
            return 0
        
        command = parse_lineparse(line)
        if dispatch(command) == False:
            return 0
   

if __name__ == "__main__":
    raise SystemExit(repl_loop())