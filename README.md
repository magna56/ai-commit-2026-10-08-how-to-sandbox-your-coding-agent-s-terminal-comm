# How to Sandbox Your Coding Agent's Terminal Commands

**TL;DR:** VS Code can now restrict the files and hosts your agent's terminal commands reach, separately from whether you approved the command. Turn it on. Then notice that your git config, your CI workflows and your package manifest all sit inside the line it draws.

Published from [The AI Commit](https://theaicommit.com/#2026-10-08/code) — Coding Agents & Productivity, 2026-10-08.

## Run

```bash
python3 code_example.py
```

## Output

```
Workspace: /repo
Allow-list: registry.npmjs.org, pypi.org, github.com

  action                               sandbox    your team calls it
  ----------------------------------------------------------------------
  write ~/.aws/credentials             BLOCKS     a breach
  write ~/.ssh/authorized_keys         BLOCKS     a breach
  curl an unrecognized host            BLOCKS     a breach
  rewrite .github/workflows/ci.yml     permits    a breach
  repoint .git/config remote           permits    a breach
  add a postinstall to package.json    permits    a breach
  git push                             permits    a breach
  npm publish                          permits    a breach
  edit src/billing/webhook.ts          permits    normal work
  npm install from the registry        permits    normal work

  Blocked: 3 of 8 breaches.
  Still reachable: 5 of 8.

  Every one still reachable is inside the workspace or on the
  allow-list, which is not a gap in the sandbox. It is where the
  sandbox draws its line, working exactly as documented.

--- what needs a second control, and which one ---
  rewrite .github/workflows/ci.yml     runs later in CI, on a machine with no sandbox
  repoint .git/config remote           controls where a push goes
  add a postinstall to package.json    a postinstall hook runs on every install
  git push                             a push leaves the machine
  npm publish                          a publish leaves the machine

  These are ordinary problems with ordinary answers: code owners on
  the workflow files and the manifest, branch protection on the push,
  a reviewed lockfile. None of them is a sandbox setting.

--- the rollout bug worth checking first ---
  chat.agent.sandbox.enabled         macOS, Linux, WSL2 (preview)
  chat.agent.sandbox.enabledWindows  Windows (experimental)
  Set only the first one org-wide and every Windows developer is
  unsandboxed, with nothing anywhere saying so.

```

## Code

See [`code_example.py`](code_example.py).
