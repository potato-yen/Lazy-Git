import subprocess

def command_run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def is_git_repo():
    r = command_run(["git", "rev-parse", "--is-inside-work-tree"])
    return r.returncode == 0 and r.stdout.strip() == "true"

def list_branches():
    if not is_git_repo():
        return []

    r = command_run(["git", "for-each-ref", "--format=%(refname:short)", "refs/heads"])
    if r.returncode != 0:
        return []

    branches = []
    for line in r.stdout.splitlines():
        name = line.strip()
        if name:
            branches.append(name)
    return branches

def list_commits(limit):
    if limit <= 0:
        return []
    if not is_git_repo():
        return []

    r = command_run(["git", "log", "--oneline", f"-n{limit}"])
    if r.returncode != 0:
        return []

    commits = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        sha, _, msg = line.partition(" ")
        commits.append((sha.strip(), msg.strip()))
    return commits
