# test_adapter.py
from __future__ import annotations

import os
import sys
import argparse
from pathlib import Path

# TODO: 改成你自己的模組名，例如:
# import git_adapter as ga
import git_adapter as ga  # <-- 你如果檔名不是 git_adapter.py，改這行

def _chdir_to_target(target: str | None) -> None:
    if target is None:
        return
    p = Path(target).expanduser().resolve()
    if not p.exists() or not p.is_dir():
        print(f"[ERROR] target path not a directory: {p}")
        sys.exit(2)
    os.chdir(p)

def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def main() -> int:
    ap = argparse.ArgumentParser(description="Test LazyGit Git Adapter functions")
    ap.add_argument("--path", help="cd to this path before testing (should be a git repo)")
    ap.add_argument("--branches", type=int, default=10, help="how many branches to print")
    ap.add_argument("--commits", type=int, default=10, help="how many commits to print")
    args = ap.parse_args()

    _chdir_to_target(args.path)
    cwd = Path.cwd()

    _print_header(f"Working Directory: {cwd}")

    # 1) is_git_repo()
    _print_header("1) is_git_repo()")
    try:
        ok = ga.is_git_repo()
        print(f"is_git_repo() -> {ok!r}")
    except Exception as e:
        print(f"[EXCEPTION] is_git_repo() raised: {type(e).__name__}: {e}")
        return 1

    # 2) list_branches()
    _print_header("2) list_branches()")
    try:
        branches = ga.list_branches()
        if not isinstance(branches, list) or any(not isinstance(b, str) for b in branches):
            print("[FAIL] list_branches() should return list[str]")
            print(f"  got type={type(branches)} sample={branches[:3] if hasattr(branches,'__getitem__') else branches}")
            return 1

        print(f"Total branches: {len(branches)}")
        for i, b in enumerate(branches[: args.branches], 1):
            # 基本衛生檢查：不應包含 '*' 或換行
            bad = ("*" in b) or ("\n" in b) or ("\r" in b) or (b.strip() != b)
            mark = "  [SUSPECT]" if bad else ""
            print(f"{i:>2}. {b}{mark}")

        # 小檢查：重複分支名
        dup = len(branches) != len(set(branches))
        print(f"Duplicate branch names? {dup}")

    except Exception as e:
        print(f"[EXCEPTION] list_branches() raised: {type(e).__name__}: {e}")
        # 如果你策略是「不是 repo 就丟例外」，這裡也會看到
        return 1

    # 3) list_commits(limit)
    _print_header("3) list_commits(limit)")
    try:
        commits = ga.list_commits(args.commits)
        if not isinstance(commits, list):
            print("[FAIL] list_commits() should return list[tuple[str, str]]")
            print(f"  got type={type(commits)} value={commits}")
            return 1

        # 檢查每筆格式
        bad_rows = 0
        for row in commits:
            if (
                not isinstance(row, tuple)
                or len(row) != 2
                or not isinstance(row[0], str)
                or not isinstance(row[1], str)
            ):
                bad_rows += 1

        if bad_rows:
            print(f"[FAIL] list_commits() has {bad_rows} invalid rows (expected (sha:str, subject:str))")
            print(f"  sample={commits[:3]}")
            return 1

        print(f"Returned commits: {len(commits)} (limit requested: {args.commits})")
        for i, (sha, subject) in enumerate(commits, 1):
            # sha 基本檢查：通常是 7~40 的 hex（不做強校驗，先抓大方向）
            sha_ok = (7 <= len(sha) <= 40) and all(c in "0123456789abcdefABCDEF" for c in sha)
            subj_ok = (subject.strip() == subject) and ("\n" not in subject) and ("\r" not in subject)

            flags = []
            if not sha_ok:
                flags.append("sha?")
            if not subj_ok:
                flags.append("subject?")
            flag_txt = f"  [SUSPECT:{','.join(flags)}]" if flags else ""

            print(f"{i:>2}. {sha}  {subject}{flag_txt}")

    except Exception as e:
        print(f"[EXCEPTION] list_commits() raised: {type(e).__name__}: {e}")
        return 1

    _print_header("RESULT")
    print("All checks passed (basic structural checks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
