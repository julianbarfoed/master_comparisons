# Working agreements

This is an audio web app and a practice project for parallel agent development.
Read `README.md` and the task brief supplied for your current assignment.
These guidelines describe how to work; feature specs and technology choices belong
in the task brief, not in this file.

## Scope and ownership

- Follow the goal, ownership boundaries, and acceptance criteria in your assignment.
- Agree on interfaces with dependent tasks before implementing incompatible changes.
- Flag changes needed outside your assigned paths to the coordinator. Shared files
  such as dependency manifests, settings, and application wiring need a named owner
  for each round of work.
- Avoid unrelated cleanup and preserve other people's changes.

## Small PRs

- Give each PR one clear purpose and keep it independently reviewable and working.
- Split large assignments into successive PRs; an agent does not need to deliver
  its entire area in one PR. Include relevant tests and docs with each change.
- Add dependencies, abstractions, and tooling only when the current change needs them.
- Start with a small end-to-end step. Run agents in parallel when their next tasks
  have clear, independent scopes; the five-agent split is optional, not a launch quota.

## Workflow

- Use one task branch and one worktree per agent. Do not switch or edit another
  agent's worktree. The main checkout is reserved for coordination and review.
- Install dependencies inside your worktree. Keep local data, credentials, and
  generated outputs ignored. Never use production services for tests.
- Run the checks relevant to your changes. Backend: `make check-backend`.
  Frontend: `make check-frontend`. Document any additional checks you introduce.
- Tests must cover observable behavior and meaningful failure paths. Tests must
  use temporary storage and must not depend on an existing personal audio library.
- Before handoff, inspect `git diff --check` and your diff. Commit only scoped files.
- When authorized to publish, push the task branch and open a PR using the template.
  Include exact checks and outcomes; distinguish implemented behavior from plans.
- Leave merging to the user. Do not resolve cross-agent ownership conflicts by
  overwriting another agent's work; send a concise handoff with the affected paths.

## Design

- Prefer small, testable modules and explicit boundaries between components.
- Follow existing conventions; introduce structure when the assigned work needs it.
- Keep service-specific details behind interfaces that tests can replace.
- Report assumptions and dependencies in your handoff, including what was mocked
  and what was verified against another component or real service.
