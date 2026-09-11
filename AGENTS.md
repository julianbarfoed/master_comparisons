# Working agreements

Read `README.md`, `docs/ROADMAP.md`, and the current assignment before changing code.

## Communication and documentation

- Ask questions and discuss alternatives in chat. Record settled decisions in docs.
- README owns operating instructions; ROADMAP owns shared architecture, contracts,
  milestones, and current priorities; this file owns durable working rules.
- Keep details beside the code when future maintainers need them. Avoid duplicate
  guides, archived PR descriptions, and documents without an active consumer.
- PR descriptions explain the resulting solution, validation, and concrete
  dependencies. Resolve planning questions in chat before publishing the solution.

## Implementation and review

- Give each PR one meaningful capability or a named consumer in the roadmap.
  Keep it reviewable; there is no line-count target or PR quota.
- Include relevant tests and docs with the change. Add tooling and abstractions
  when the current feature needs them.
- Use a separate task branch/worktree from current main; preserve other agents'
  changes. Agree owned paths and shared interfaces before parallel implementation.
- Give shared configuration, dependency files, and app wiring one writer per wave.
  Coordinate changes outside your scope with that owner.
- Use isolated test data and development services; keep credentials out of Git.
- Run relevant checks from README and `git diff --check`. Distinguish mocked
  verification from real integration evidence.
- Every implementation assignment includes delivery: run checks, commit scoped
  changes, push the task branch, and open a PR for the user to review. Return the
  PR link with validation results and any limitations; local commits alone are not
  completion. If publishing is blocked, report the blocker in chat.
- Review-only assignments do not require a PR. Follow any explicit instruction
  to keep work local. Leave merging to the user; start the next task from updated main.
