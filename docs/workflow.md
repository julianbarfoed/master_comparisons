# Agent worktrees and review

## Starting point

Merge the foundation PR into `main` first. Keep the main checkout for coordination.
Use three tmux panes (backend, frontend, QA) and one optional pane for servers/logs.
Each pane must start its agent in a separate worktree, not merely a separate shell
in the same directory.

From the main repository, after the foundation is merged:

```sh
git switch main
git pull --ff-only
mkdir -p .worktrees
git worktree add .worktrees/backend -b feat/audio-backend main
git worktree add .worktrees/frontend -b feat/audio-frontend main
git worktree add .worktrees/qa -b test/audio-e2e main
```

`.worktrees/` is ignored. These checkouts are inside the workspace so local agents
can access them under the same workspace permissions. Do not run multiple agents
inside any one checkout. Branch names and paths above are for a fresh setup; use
`git worktree list` before rerunning commands.

In each pane, `cd` into the appropriate worktree and run `codex`. Give the agent:

> Read AGENTS.md, docs/api.md, and docs/tasks/<your-role>.md. Implement that task in
> this worktree only. Run its checks, commit your changes, push this task branch,
> and open a PR for my review. Do not merge. Report contract changes before making
> them and report any blockers with the affected paths.

Run `make setup-backend` or `make setup-frontend` in each relevant worktree. QA
uses `make setup` plus its own browser test setup. Ignored `.env` files and installed
dependencies are not copied by ordinary Git worktree creation. Use the examples;
this milestone needs no credentials. Use temporary test data instead of copying a
personal library.

## Coordinating

Backend and frontend start together. Frontend uses API mocks while backend is
under development. QA builds tests against the contract without editing app code.
The coordinator owns shared docs and CI changes requested by agents.

If several app instances run at once, use different port pairs and matching origins.
For example, from a backend worktree's `back-end/`:

```sh
WEB_ORIGIN=http://localhost:5174 .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

And from its frontend directory:

```sh
VITE_API_URL=http://localhost:8001 npm run dev -- --host 127.0.0.1 --port 5174
```

The backend agent implements origin configuration as part of the API task. Storage
must remain local to each worktree or a test's temporary directory. Ordinary browser
and API servers for a single integration run may simply use ports 5173 and 8000.

## Review and integration

1. Each agent checks its own changes and opens one focused PR. Use the PR template.
2. Open that agent's worktree in VS Code, e.g. `code -n .worktrees/backend`, to
   inspect/run its branch. Do not check out the same branch in the main checkout.
3. Before merging app PRs, the coordinator creates a disposable integration branch
   in a fourth worktree and merges the candidate branches there. QA's tests run
   against that combined checkout. Candidate merge commits stay off task branches.
4. Send failures to the relevant owner. Update the candidates and rerun affected
   checks. QA reports the exact candidate commits it tested.
5. The user merges reviewed PRs one at a time. Update remaining task branches from
   `origin/main`, then rerun their relevant checks. Run the complete flow on the
   final merged state before declaring the milestone finished.
6. Once work is merged and a worktree is clean, stop its servers and use
   `git worktree remove <exact-path>`. Remove obsolete branches afterward. Never
   delete a worktree that contains uncommitted work.

QA may prepare its tests before app implementations exist. It must clearly report
which checks are blocked on implementation rather than marking them as passing.
Adding browser checks to shared CI is a coordinator handoff after they run reliably.

## Publishing the foundation

The setup branch is `chore/agent-foundation`. After its local checks pass:

```sh
gh auth login
git push -u origin chore/agent-foundation
gh pr create --base main --head chore/agent-foundation --title "Prepare audio app for parallel agent development" --body-file docs/foundation-pr.md
```

Only authenticate if needed (`gh auth status`). The user reviews and merges the
foundation before the three feature worktrees are created.
