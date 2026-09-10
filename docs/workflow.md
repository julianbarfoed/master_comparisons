# Agent worktrees and review

Use the [product roadmap](ROADMAP.md) for shared direction and dependencies. A task
brief selects a meaningful part of the current milestone; it does not independently
invent provider choices or competing interfaces. Refine acceptance criteria using the
[task brief template](tasks/TEMPLATE.md). Briefs can live in launch prompts or in
task documents when several agents need to reference the same decisions.

## Before launching agents

1. Choose the outcome for this round and decide which parts can run independently.
2. Give each agent owned paths, its tests, and a clear completion condition.
3. Agree on the interfaces that cross ownership boundaries: inputs, outputs,
   errors, and who implements each side. A small shared note is usually enough;
   add typed interfaces or schemas when useful.
4. Assign one owner to shared dependency/config files and final integration. Supply
   the same decisions to every affected agent; separate sessions need handoffs.

These are launch decisions, not a requirement to specify the entire app in advance.
Agents can investigate options first if a provider or approach has not been chosen.

## Example: five agents

This is a map of available specialties, not a requirement to launch five PRs per
round. The roadmap determines which agents have useful parallel work. Refine paths
and deliverables in the actual assignments; this role map does not select a
database, auth provider, HTTP API, upload flow, or schema.

| Agent | Area of ownership | Interface to agree before implementation |
| --- | --- | --- |
| Auth | Backend identity/token validation and its tests | How consumers obtain a verified identity and distinguish auth failures |
| Database | Persistence, migrations, and repository tests | Data needed by consumers and repository operations, including ownership fields if required |
| R2 | Object-storage adapter and its tests | Object identifiers, transfer/access operations, and failure behavior |
| API | HTTP routes, application wiring, and API tests | Browser-facing requests/responses and how auth, database, and storage are called |
| Frontend | UI, browser auth integration, API client, and UI tests | API payloads and the browser/server auth flow |

The existing `back-end/app/auth.py`, `db.py`, and `storage.py` are starting points
for the first three areas; `main.py` and `front-end/` anchor the other two. Agents
may introduce modules as their tasks grow. Frontend owns login UI; the auth agent
coordinates the identity flow rather than editing the same frontend files.

For this split, the coordinator can own `back-end/pyproject.toml`, shared settings,
root tooling, and CI. Agree dependency additions at launch or hand them back to the
coordinator. The API agent owns application wiring. This avoids several agents
independently rewriting the same startup/configuration files.

Once boundaries are agreed, all five can implement concurrently. API tests can use
fake auth/repository/storage providers; frontend tests can mock API responses.
Mocks let implementation proceed, but completion still requires testing the real
components together. The API/coordinator integration pass is a dependency even
when the coding was parallel.

## Worktree setup

Merge the foundation first. Keep the main checkout for coordination. Create one
branch and worktree per assignment, for example from an up-to-date `main`:

```sh
git worktree add .worktrees/auth -b feat/auth main
git worktree add .worktrees/db -b feat/db main
git worktree add .worktrees/r2 -b feat/r2 main
git worktree add .worktrees/api -b feat/api main
git worktree add .worktrees/frontend -b feat/frontend main
```

These are examples for a fresh round; check `git worktree list` before reusing paths
or names. `.worktrees/` is ignored and stays inside the workspace. In each tmux pane,
enter the corresponding worktree, start an agent, and supply its completed brief.
Never run independent agents in the same checkout.

Run `make setup-backend`, `make setup-frontend`, or `make setup` as relevant inside
each worktree. Dependencies and ignored environment files are not copied by ordinary
Git worktree creation. Configure only the development services required by the
assignment. Separate ports and test data when multiple instances run concurrently;
worktrees isolate files, not processes, ports, databases, or cloud resources.

## Handoff and review

1. Each agent runs relevant checks and hands off its changes, interface notes, and
   any remaining dependencies. Commit, push, and open one focused PR when authorized.
2. Open the worktree directly in VS Code, e.g. `code -n .worktrees/auth`. Do not try
   to check out its branch simultaneously in the main checkout.
3. The coordinator assembles candidate branches in a separate integration worktree
   and runs the agreed flow using real components. Keep those temporary merge
   commits off the individual task branches. Return fixes to the owning agents.
4. The user reviews and merges PRs. Update remaining branches from `main` as needed
   and check the final combined state. Report which commits were integration-tested.
5. Stop servers and remove clean, completed worktrees with `git worktree remove
   <exact-path>` after their work is merged. Preserve any uncommitted work.

No separate QA agent is required for this split: each agent owns its tests, and the
coordinator owns the integration check. Add a reviewer/QA assignment if useful.
