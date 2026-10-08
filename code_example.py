"""Work out what your coding agent's terminal sandbox actually leaves reachable.

VS Code 1.141 added sandboxing for agent terminal commands. It is governed by
two published defaults: file writes outside the workspace need approval
(`chat.tools.terminal.blockDetectedFileWrites` defaults to "outsideWorkspace"),
and network access is bounded by an allow-list (`chat.agent.networkFilter` with
`chat.agent.allowedNetworkDomains`).

Both limits are drawn around a LOCATION. That is the part worth checking rather
than assuming, because a handful of high-value paths sit inside the workspace
and a push and a publish both travel over hosts you had to allow.

Point `audit` at your own workspace layout and allow-list before you decide the
sandbox has bought you enough to raise your approval level.

Run: python3 code_example.py        (stdlib only, no network, no API key)
"""

import posixpath
from dataclasses import dataclass

WORKSPACE = "/repo"

# A realistic allow-list: the registry you install from, the forge you push to.
ALLOWED_DOMAINS = ["registry.npmjs.org", "pypi.org", "github.com"]

# Paths that live inside the workspace but are not ordinary source. Each one is
# read later by something that is NOT sandboxed, which is what makes it matter.
# Tune this list to your repo -- it is the whole point of the exercise.
ESCALATING_PATHS = {
    ".github/workflows/": "runs later in CI, on a machine with no sandbox",
    ".git/config": "controls where a push goes",
    "package.json": "a postinstall hook runs on every install",
    "Makefile": "run by hand and by CI, usually without review",
}

# Hosts that are on the allow-list for a good reason and still reach outward.
EGRESS_CAPABLE = {
    "github.com": "a push leaves the machine",
    "registry.npmjs.org": "a publish leaves the machine",
}


@dataclass
class Action:
    label: str
    target: str          # an absolute path, or a hostname
    breach: bool         # would your team call this an incident?


def is_path(target):
    return target.startswith("/")


def sandbox_permits(target, workspace=WORKSPACE, allowed=None):
    """The documented default policy, and nothing more."""
    allowed = ALLOWED_DOMAINS if allowed is None else allowed
    if is_path(target):
        return target == workspace or target.startswith(workspace + "/")
    return target in allowed


def escalating(target, workspace=WORKSPACE):
    """Inside the boundary, but read later by something outside it."""
    if is_path(target):
        rel = posixpath.relpath(target, workspace)
        for path, why in ESCALATING_PATHS.items():
            if rel == path or rel.startswith(path):
                return why
        return None
    return EGRESS_CAPABLE.get(target)


ACTIONS = [
    Action("write ~/.aws/credentials", "/home/u/.aws/credentials", True),
    Action("write ~/.ssh/authorized_keys", "/home/u/.ssh/authorized_keys", True),
    Action("curl an unrecognized host", "paste.example.com", True),
    Action("rewrite .github/workflows/ci.yml", "/repo/.github/workflows/ci.yml", True),
    Action("repoint .git/config remote", "/repo/.git/config", True),
    Action("add a postinstall to package.json", "/repo/package.json", True),
    Action("git push", "github.com", True),
    Action("npm publish", "registry.npmjs.org", True),
    Action("edit src/billing/webhook.ts", "/repo/src/billing/webhook.ts", False),
    Action("npm install from the registry", "registry.npmjs.org", False),
]


def audit(actions, workspace=WORKSPACE, allowed=None):
    rows, missed = [], 0
    for a in actions:
        permitted = sandbox_permits(a.target, workspace, allowed)
        why = escalating(a.target, workspace) if permitted else None
        if permitted and a.breach:
            missed += 1
        rows.append((a, permitted, why))
    return rows, missed


def main():
    rows, missed = audit(ACTIONS)
    print(f"Workspace: {WORKSPACE}")
    print(f"Allow-list: {', '.join(ALLOWED_DOMAINS)}\n")
    print(f"  {'action':<36} {'sandbox':<10} {'your team calls it'}")
    print("  " + "-" * 70)
    for a, permitted, _ in rows:
        print(f"  {a.label:<36} {('permits' if permitted else 'BLOCKS'):<10} "
              f"{'a breach' if a.breach else 'normal work'}")

    total = sum(1 for a in ACTIONS if a.breach)
    print(f"\n  Blocked: {total - missed} of {total} breaches.")
    print(f"  Still reachable: {missed} of {total}.\n")
    print("  Every one still reachable is inside the workspace or on the")
    print("  allow-list, which is not a gap in the sandbox. It is where the")
    print("  sandbox draws its line, working exactly as documented.\n")

    print("--- what needs a second control, and which one ---")
    for a, permitted, why in rows:
        if permitted and a.breach:
            print(f"  {a.label:<36} {why}")
    print("\n  These are ordinary problems with ordinary answers: code owners on")
    print("  the workflow files and the manifest, branch protection on the push,")
    print("  a reviewed lockfile. None of them is a sandbox setting.")

    print("\n--- the rollout bug worth checking first ---")
    print("  chat.agent.sandbox.enabled         macOS, Linux, WSL2 (preview)")
    print("  chat.agent.sandbox.enabledWindows  Windows (experimental)")
    print("  Set only the first one org-wide and every Windows developer is")
    print("  unsandboxed, with nothing anywhere saying so.")


if __name__ == "__main__":
    main()
