# Agent Skills

Reusable agent skills for Claude Code, Codex, and other runtimes that support the Agent Skills directory layout.

This repository is organized as an APM package:

```text
.apm/skills/<skill-name>/SKILL.md
```

## Skills

- `ghostty-applescript` - write Ghostty AppleScript layout scripts.
- `cloudwatch-logs-insights-query` - write and validate CloudWatch Logs Insights QL queries.
- `goal-template-generator` - turn rough work requests into execution-ready GOAL templates.
- `prompt-refiner` - refine rough coding requests into prompts for another coding agent.
- `non-committed-analyzer` - inspect uncommitted changes and propose commit splits.
- `yarn-classic-to-pnpm` - migrate or audit Yarn Classic to pnpm dependency drift.
- `isis` - investigate issues and tickets as hypotheses before implementation.
- `codex-exec` - delegate rescue/review tasks to Codex CLI.
- `codex-collab-review` - run a Claude Code and Codex CLI collaborative review workflow.
- `commit-push` - commit and push only files changed in the current thread.
- `harness-creator` - build verification harnesses with mechanical Red/Green checks.
- `ggg` - force web-backed answers for freshness-sensitive questions.

## Install With APM

```sh
apm install TeXmeijin/agent-skills --target agent-skills,claude,codex
```

For user-scope install:

```sh
apm install -g TeXmeijin/agent-skills --target agent-skills,claude,codex
```

## Local Development

For local authoring, keep this repository as the source of truth and symlink the skill directories into the runtime locations:

```sh
./scripts/link-local.sh
```

The script backs up existing real directories before replacing them with symlinks.

