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


def remove_label(remote_names: list[str], remote_branches: list[str], local_branches: list[str]) -> dict[str, list[str]]:
    categorized: dict[str, list[str]] = {"local": list(local_branches)}

    remote_set = set(remote_names)
    for r in remote_names:
        categorized.setdefault(r, [])

    for full in remote_branches:
        if "/" not in full:
            continue
        remote, branch = full.split("/", 1)

        if remote not in remote_set:
            continue

        categorized[remote].append(branch)

    return categorized

