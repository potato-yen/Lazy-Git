import subprocess


def command_run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True)


def is_git_repo() -> bool:
    output = command_run(["git", "rev-parse", "--is-inside-work-tree"])
    return output.returncode == 0 and output.stdout.strip() == "true"


def list_remote_names() -> list[str]:
    if not is_git_repo():
        return []
    
    output = command_run(["git", "remote"])
    if output.returncode != 0:
        return []
    
    remote_names = []
    for line in output.stdout.splitlines():
        name = line.strip()
        if name:
            remote_names.append(name)
    return remote_names


def list_local_branches() -> list[str]:
    if not is_git_repo():
        return []
    
    output = command_run(["git", "for-each-ref", "--format=%(refname:short)", "refs/heads"])
    if output.returncode != 0:
        return []
    
    branches = []
    for line in output.stdout.splitlines():
        name = line.strip()
        if name:
            branches.append(name)
    
    return branches


def list_remote_branches() -> list[str]:
    if not is_git_repo():
        return []
    
    output = command_run(["git", "for-each-ref", "--format=%(refname:short)", "refs/remotes"])
    if output.returncode != 0:
        return []
    
    branches = []
    remote_names = list_remote_names()
    for line in output.stdout.splitlines():
        name = line.strip()
        if not name:
            continue

        if name.endswith("/HEAD"):
            continue

        if name in remote_names:
            continue

        branches.append(name)
    
    return branches


def list_branches() -> list[str]:
    if not is_git_repo():
        return []

    branches = list_local_branches() + list_remote_branches()
    return branches


def list_commits(limit: int) -> list[tuple[str, str]]:
    if limit <= 0:
        return []
    if not is_git_repo():
        return []

    output = command_run(["git", "log", "--oneline", "-n", str(limit)])
    if output.returncode != 0:
        return []

    commits = []
    for line in output.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        hash, _, msg = line.partition(" ")
        commits.append((hash.strip(), msg.strip()))
    return commits


def checkout(branch: str) -> tuple[int, str, str]:
    if not is_git_repo():
        return (1, "", "Not a git repository.")
    output = command_run(["git", "checkout", branch])
    return (output.returncode, output.stdout, output.stderr)


def reset(sha: str) -> tuple[int, str, str]:
    if not is_git_repo():
        return (1, "", "Not a git repository.")
    output = command_run(["git", "reset", sha])
    return output.returncode, output.stdout, output.stderr


def status() -> tuple[int, str, str]:
    if not is_git_repo():
        return (1, "", "Not a git repository.")
    output = command_run(["git", "status", "-sb"])
    return output.returncode, output.stdout, output.stderr


def fetch() -> tuple[int, str, str]:
    if not is_git_repo():
        return (1, "", "Not a git repository.")
    output = command_run(["git", "fetch", "--all", "--prune"])
    return output.returncode, output.stdout, output.stderr


def push(remote_name: str, branch: str) -> tuple[int, str, str]:
    if not is_git_repo():
        return (1, "", "Not a git repository.")
    output = command_run(["git", "push", remote_name, branch])
    return output.returncode, output.stdout, output.stderr


def pull(remote_name: str, branch: str) -> tuple[int, str, str]:
    if not is_git_repo():
        return (1, "", "Not a git repository.")
    output = command_run(["git", "pull", remote_name, branch])
    return output.returncode, output.stdout, output.stderr


def new_branch(branch: str) -> tuple[int, str, str]:
    if not is_git_repo():
        return (1, "", "Not a git repository.")
    output = command_run(["git", "branch", branch])
    return output.returncode, output.stdout, output.stderr
