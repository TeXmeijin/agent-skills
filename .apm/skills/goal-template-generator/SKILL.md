---
name: goal-template-generator
description: "Generate an execution-ready GOAL template before work begins. Use this whenever the user mentions GOAL, /goal, task template, work brief, execution prompt, agent handoff, or when a request is multi-step, high-impact, security-sensitive, investigative, verification-heavy, or likely to suffer from vague success criteria. The skill turns a rough task into GOAL / CONTEXT / CONSTRAINTS / PRIORITY / PLAN / DONE WHEN / VERIFY / OUTPUT / STOP RULES, with uncertainties and recommended defaults made explicit."
user-invocable: true
---

# Goal Template Generator

Use this skill to turn a rough request into a task-specific GOAL template that another AI agent can execute safely. The template is useful even when the runtime does not support a native `/goal` command: it is a compact instruction sheet for the work.

The goal is not to make every task bureaucratic. The goal is to prevent the common failure modes of agent work: unclear scope, invented assumptions, shallow investigation, unverified fixes, accidental side effects, and vague final reports.

## When To Use

Generate a GOAL template before execution when any of these are true:

- The user explicitly says `GOAL`, `/goal`, `task template`, `execution prompt`, `agent handoff`, `prompt for another agent`, or similar.
- The task has multiple steps, touches several files/systems, or may take more than one focused pass.
- Success criteria are vague: "make it better", "check if this is right", "fix properly", "investigate thoroughly".
- The task is security-sensitive, permission-sensitive, data-sensitive, or may expose secrets or personal information.
- The task is mainly investigation, diagnosis, verification, QA, code review, or release readiness.
- The task involves external side effects: deletion, posting, deployment, production data, cloud changes, billing, app-store/release operations, or messages to third parties.
- The user is asking for work that may be reused as a recurring workflow.

For very small and obvious tasks, do not force a long template. Produce a compact version with only the sections that reduce risk.

## Operating Mode

1. Classify the request.
2. Identify the risk level.
3. Run the Pre-GOAL Fact Pass before writing GOAL, CONTEXT, CONSTRAINTS, DONE WHEN, or VERIFY.
4. Separate user decisions from facts that the agent can fetch independently.
5. Ask the user only for unresolved upper-layer decisions that materially shape the GOAL.
6. Generate the GOAL template only after facts and required decisions are clear enough.
7. If the user asked for a prompt to paste into another agent, include a copy-paste-ready execution prompt.
8. Do not start executing the underlying work unless the user explicitly asks to proceed after the template, or the current interaction clearly requires both template generation and execution.

When the task itself is to make a plan or prompt, the GOAL template is the deliverable. When the user asked to execute a risky task directly, first produce the template and ask for acknowledgement only if the unresolved uncertainty can materially change the outcome.

## Pre-GOAL Fact Pass

Do not invent the upper-layer purpose, constraints, environment, or verification plan from vibes. A GOAL template is valuable because it freezes the right objective and boundaries. If those cannot be supported by the user's instruction, referenced materials, source code, logs, issues, docs, or quickly available command output, gather facts first or ask.

Before generating the template, collect the cheap, relevant facts that can be obtained without meaningful side effects. Use parallel reads/searches/CLI calls when possible.

Cheap facts include:

- Referenced files, code symbols, config, tests, docs, issue/PR text, comments, diffs, and local notes.
- Current branch, repository state, package scripts, test commands, CI/workflow definitions, and environment names.
- Read-only cloud or ops facts that the user has authorized or that the environment already exposes, such as `aws ... describe/get/list`, log queries, deployment metadata, or resource configuration.
- Official documentation for current third-party behavior when version-sensitive.
- Existing project rules such as AGENTS.md, CLAUDE.md, README, CONTINUITY, or local skill instructions.
- Current project instructions that materially affect safety, authority, verification, or handoff. Do not collect low-level personal workflow preferences unless the user explicitly made them part of the task.

Do not count a fact as uncertain if it is quickly fetchable. Fetch it first. Examples of bad UNCERTAINTIES:

- "Need to know which AWS resource is affected" when an authorized read-only AWS CLI command can list it.
- "Need to know the current implementation" when the file path or symbol can be searched.
- "Need to know verification command" when package scripts, CI config, or README can be inspected.

If a fact cannot be fetched because of missing credentials, unavailable network, sandbox restrictions, or insufficient permission, say exactly what was attempted and move it to `BLOCKED FACTS`, not `UNCERTAINTIES`.

## Purpose And Constraint Discipline

GOAL, CONTEXT, and CONSTRAINTS must be evidence-backed.

- If the user's stated purpose is explicit, preserve it.
- If the purpose is inferable from a referenced issue, code, incident, or document, cite the source in CONTEXT.
- If the purpose is only a guess, do not present it as GOAL. Put it in `DECISIONS NEEDED` with a recommended interpretation.
- Do not decide product policy, security posture, release policy, acceptable risk, or business priority on the user's behalf.
- Do not turn low-level implementation details into upper-layer purpose. "Run AWS CLI and inspect WAF logs" is a means; the GOAL might be "determine whether staging app requests are being blocked by WAF" only if the prompt or evidence supports it.
- Constraints should come from user instruction, project rules, codebase conventions, platform requirements, or safety defaults. If a constraint is merely prudent but not known to be required, label it as a default safety constraint.

## Internal Consistency Pass

Before returning the template, run a consistency pass over the generated GOAL. This is mandatory for long templates and high-risk work.

Check for:

- **Capability mismatch**: The GOAL tells the next agent to perform work it cannot do, such as creating cloud resources without write credentials. Rewrite those steps as "prepare instructions for the user" or "request approval/credentials" instead.
- **Phase mismatch**: The same phase number or label means different things in different sections. Rename phases so the workflow is unambiguous.
- **Decision mismatch**: An item is listed under `UNCERTAINTIES` but says `Needs user confirmation: no`. That is not an uncertainty; move it to `CONFIRMED FACTS`, `ASSUMPTIONS`, `DEFAULT DECISIONS`, or `PLAN`.
- **Constraint mismatch**: The GOAL encourages an action that a later constraint forbids, such as "aggressively try infrastructure changes" while also saying "no cloud writes".
- **Tool mismatch**: The GOAL hardcodes local tools, skills, paths, or UI workflows without verifying they exist. Either verify them first, state a fallback path, or omit the low-level command entirely.
- **Workflow mismatch**: The GOAL bakes in personal machine conventions that do not belong in a reusable task template. Keep the GOAL focused on purpose, constraints, authority boundaries, verification, and stop rules; leave incidental command style to the executing agent unless it is safety-critical or explicitly requested.
- **Secret-handling mismatch**: Any command that touches tokens, API keys, credentials, or private data must be checked for shell history, logs, process list exposure, issue/comment leakage, and committed diffs.
- **Approval mismatch**: A recommendation is treated as an approved decision before the user or required reviewer has approved it.

If the consistency pass finds a mismatch, fix the template before showing it. Do not leave contradictions for the next agent to discover.

## Delivery Mode

Default to returning the GOAL template in chat as Markdown. Do not create or modify files just because this skill produced Markdown.

Create a Markdown file only when the user explicitly asks to save it, asks for a reusable template library, or the surrounding project instructions clearly require persistent notes. If saving, state the path and keep the file free of secrets, private data, and internal-only names unless the user intentionally wants a local private artifact.

For long, high-risk, or review-heavy templates, prefer producing a reviewable Markdown artifact and sending it through the user's available review workflow when the user asks for review or iteration. A review pass is useful when the GOAL contains many phases, HITL loops, secrets, cloud operations, or issue/PR comment rewrites. Treat review comments as requirements until resolved or explicitly rejected.

After producing the template, the expected next step is:

- The user can paste it into another agent or a native GOAL command.
- The user can reply with changes to tighten scope, constraints, or verification.
- The user can say to proceed, at which point the agent executes according to the template.
- The user can save it as a reusable workflow if the task is recurring.
- The user can review/comment on the template, and the agent should revise the template before treating it as final.

## Classification

Pick one primary task type. Add secondary types only if they change constraints or verification.

- `code-change`: modify application/library code.
- `security-change`: fix or assess auth, permissions, secret handling, injection, data exposure, paid-feature bypass, abuse prevention, or vulnerability reports.
- `investigation`: determine facts, causes, feasibility, or tradeoffs.
- `verification`: prove behavior through tests, logs, screenshots, manual scenarios, or reproducible commands.
- `review`: evaluate a PR, issue, design, implementation, incident note, or agent output.
- `configuration`: dotfiles, editor, shell, CI, infrastructure-as-code, project settings.
- `release-or-ops`: deploy, publish, app store, cloud, production, billing, credentials.
- `knowledge-work`: summarize, research, write notes, prepare articles, produce learning material.
- `file-or-content-ops`: organize files, find assets, prepare a post/message, transform documents.

## Risk Levels

Use the risk level to decide how strict the template should be.

- `Low`: read-only, draft-only, local-only, easy to revise.
- `Medium`: edits files, changes configuration, adds tests, updates docs, or runs local commands.
- `High`: secrets, personal data, auth/authorization, payment, production, deletion, public posting, cloud resources, release, or broad refactors.

High-risk templates need explicit STOP RULES, a rollback or non-destructive path, and verification that includes negative cases where applicable.

## Uncertainty Handling

Do not ask open-ended questions by default. Prefer recommended defaults with rationale, but only after the Pre-GOAL Fact Pass.

Use three separate buckets:

1. `CONFIRMED FACTS`: facts gathered from user instruction, files, code, logs, docs, commands, issues, PRs, or other primary sources.
2. `BLOCKED FACTS`: facts the agent tried to gather but could not, with the reason and attempted method.
3. `DECISIONS NEEDED`: user-level choices that cannot be settled by inspection and materially affect the GOAL.
4. `DEFAULT DECISIONS`: choices the agent can safely default because the user already gave enough direction, the risk is low, or the default is reversible.

`UNCERTAINTIES` in the final template should be reserved for `DECISIONS NEEDED`, not for agent laziness or unfetched context.

Do not include an item in `UNCERTAINTIES` if `Needs user confirmation` would be `no`. Put that item in `DEFAULT DECISIONS` or fold it into the PLAN. `UNCERTAINTIES` are for unresolved user decisions or blockers that change the top-level goal, constraints, or approval boundary.

Use this shape:

```md
## CONFIRMED FACTS
- <Fact> — <source>

## BLOCKED FACTS
- <Fact needed> — <attempted method and blocker>

## DEFAULT DECISIONS
- <Default chosen without asking> — <why this is safe/reversible/evidenced>

## UNCERTAINTIES
1. <What is unclear>
   - Recommended default: <specific choice>
   - Rationale: <why this is the safest or most likely interpretation>
   - Needs user confirmation: yes/no
```

Ask the user before proceeding only when:

- The ambiguity can cause irreversible work or public/external side effects.
- The task could be solved in two materially different directions.
- A secret, credential, production system, private data, payment, or deletion is involved.
- The agent would otherwise have to invent product policy, legal/security posture, or user intent.
- The top-level GOAL or non-negotiable CONSTRAINTS cannot be stated from evidence.

## Default Constraints

Use these defaults unless the user says otherwise:

- Respect existing architecture, naming, style, and operational conventions.
- Keep changes to the minimum sufficient scope for the stated goal.
- Do not add unrelated refactors, cleanups, dependency upgrades, or broad redesigns.
- Separate verified facts from assumptions and inferences.
- Prefer static inspection before mutation: read files, diffs, issues, logs, and docs before editing or running stateful commands.
- Do not expose secrets, tokens, credentials, private URLs, customer data, personal information, or sensitive logs.
- Do not perform external posting, deletion, deployment, billing, production, or credential changes without explicit approval.
- If verification cannot be completed, say exactly what was not verified and provide the closest useful alternative.

## Task-Specific Guidance

### HITL And Approval Workflows

Use this when the task requires the user to approve choices, perform privileged operations, provide credentials out-of-band, or review generated text before publication.

The GOAL should define:

- Which decisions need explicit approval.
- Which actions the agent can do independently.
- Which actions only the user can do.
- How many loops are allowed before marking a point unresolved.
- What artifact will be reviewed: issue comment, PR, markdown file, command plan, screenshot, or checklist.

Do not hardcode a user-specific approval tool or local script unless you have verified it exists in the environment. If a local tool is useful but not guaranteed, phrase it as an option and provide a fallback, such as "use the available decision UI if present; otherwise ask in chat with numbered options."

Do not treat `Recommended default` as approval. A recommendation becomes a decision only after explicit approval, or when the template clearly classifies it as a reversible default decision that does not affect downstream risk.

When the GOAL itself is a decision artifact, include a review loop in the PLAN:

1. Produce the draft artifact.
2. Ask the user to review via the available review channel or inline chat.
3. Apply comments and reply with what changed.
4. Repeat until material comments are resolved.
5. Only then proceed to publication, issue comment update, PR, or execution.

### Security-Sensitive Work

Use this for vulnerability reports, auth/authorization, paid-feature bypasses, secret handling, abuse prevention, or permission checks.

The GOAL should distinguish:

- What is authorized to inspect or change.
- Whether the task is read-only assessment, fix implementation, or verification.
- Which threat or bypass is in scope.
- Which systems and data are explicitly out of scope.
- What negative tests or abuse cases must be checked.

Constraints to include:

- Avoid destructive proof-of-concept actions.
- Do not print or persist secrets or real private data.
- Prefer local, staging, or synthetic data for reproduction.
- Stop before production changes or credential rotation unless explicitly approved.
- Report exploitability at the level needed for remediation, not as a reusable abuse guide.
- For credential-handling commands, specify the safe transport/storage path and verify it does not leak through chat text, shell history, process listings, logs, issue comments, or commits.

### Investigation And Root Cause Work

Use this when the user asks to "investigate", "find the cause", "check if this is true", "compare options", or "validate an issue".

The PLAN should be evidence-first:

1. Collect the user's claim and expected behavior.
2. Inspect primary sources first: code, config, issue/PR text, logs, official docs, or reproducible outputs.
3. Build a timeline or dependency path if the issue crosses systems.
4. Separate facts, inferences, and unknowns.
5. Stop before implementing unless implementation is explicitly part of the goal.

The OUTPUT should include evidence references, not just conclusions.

### Verification And QA Work

Use this when the task is to prove a behavior, test a fix, confirm a release, or validate an agent's previous work.

The VERIFY section should specify:

- Exact commands, scenarios, devices, browsers, or environments.
- What passing looks like.
- What failure would look like.
- Which logs/screenshots/artifacts should be captured.
- What remains unverified if the environment is unavailable.

For UI, mobile, or E2E work, include a manual scenario with observable end state, not only automated tests.

### Code Change Work

The GOAL should name the behavior to change, not just the files to edit.

The PLAN should include:

1. Read existing implementation and adjacent tests.
2. Identify the narrowest change path.
3. Modify code in the established local style.
4. Add or update focused tests proportional to risk.
5. Run the smallest meaningful verification first, then broader checks if the change touches shared behavior.

STOP RULES should include stopping on unexpected architecture mismatch, unrelated failing tests that block confidence, or required secrets/environments that are unavailable.

### Personal Or Indie Development Work

Use this when the task is a small product, prototype, local app, side project, or workflow tool.

Optimize for useful progress without overbuilding:

- Preserve the user's current momentum and local conventions.
- Prefer small, shippable increments over platform-level abstractions.
- Make the next validation step concrete.
- Avoid expanding the product scope unless the user explicitly asks for exploration.
- If using new dependencies or frameworks, verify current official docs when the information may have changed.

### Configuration, Dotfiles, And Local Tooling

Use this for shell/editor/window manager/dotfiles/CI/config changes.

The CONTEXT should identify the source of truth and generated or managed files. The CONSTRAINTS should say not to edit generated targets when a managed source file exists. VERIFY should include a reversible check, dry run, syntax check, or command that proves the configuration loads.

### External Content Or Posting

Use this for preparing Discord/Slack/social posts, public issues, external comments, or messages.

The STOP RULES must require user confirmation before sending. The OUTPUT should separate "draft content" from "send action".

## Template Shape

Always output this structure unless a compact template is clearly better:

```md
# GOAL Template: <task name>

## CONFIRMED FACTS
- <Fact> — <source>

## BLOCKED FACTS
- <Fact needed but not obtained> — <attempted method and blocker>

## GOAL
<One clear, measurable mission. Avoid bundling unrelated outcomes.>

## CONTEXT
<Relevant repo/project, files, issue/PR/logs, user intent, current state, and prior decisions. Mark unknowns clearly.>

## UNCERTAINTIES
1. <User decision needed, not a fetchable fact>
   - Recommended default: <choice>
   - Rationale: <reason>
   - Needs user confirmation: <yes/no>

## CONSTRAINTS
- <What must not change, patterns to preserve, sensitive data rules, scope boundaries.>

## PRIORITY
1. <Highest priority, usually correctness/safety/user intent>
2. <Next priority, usually minimal scope or maintainability>
3. <Nice-to-have only if it does not expand scope>

## PLAN
1. <Understand and verify context first>
2. <Do the narrow work>
3. <Validate>
4. <Report>

## DONE WHEN
- <Observable final state>
- <No known in-scope regressions remain>

## VERIFY
- <Commands, manual checks, logs, screenshots, docs, or review steps>
- <What cannot be verified and why, if applicable>

## OUTPUT
- <What the final answer/report should contain>

## STOP RULES
- <When to stop and ask before proceeding>
```

If there are no unresolved user decisions, write:

```md
## UNCERTAINTIES
- None. The remaining unknowns are either confirmed facts, blocked facts, or default decisions captured above.
```

## Compact Template

For small tasks, use:

```md
## GOAL
<single mission>

## CONSTRAINTS
- <scope/safety constraints>

## DONE WHEN
- <completion criteria>

## VERIFY
- <how to check>

## STOP RULES
- <only if relevant>
```

## Quality Bar

Before returning the template, check:

- Is the GOAL one mission, not a bundle?
- Is the GOAL supported by confirmed facts or explicit user instruction?
- Did the agent fetch cheap facts before asking the user?
- Are fetchable missing facts listed as BLOCKED FACTS, not UNCERTAINTIES?
- Are UNCERTAINTIES actually user decisions?
- Did the consistency pass remove contradictions between GOAL, PLAN, CONSTRAINTS, HITL, and STOP RULES?
- Are user-specific tools or paths omitted unless they are safety-critical, documented project requirements, or explicitly requested?
- If the template is long or high-risk, does it define how the draft will be reviewed and revised before execution/publication?
- Are recommendations clearly separated from approved decisions?
- Are DONE WHEN and VERIFY separate?
- Are assumptions labeled?
- Are constraints strong enough for the risk level?
- Would another agent know where to stop?
- Would the user be able to judge completion from the final report?
- Is the template free of private project names, secrets, customer data, or internal-only details unless the user intentionally included them for local use?
