---
name: yarn-classic-to-pnpm
description: Use when starting a migration of an existing Yarn Classic 1.x repository or subdirectory to pnpm, or auditing a Yarn-to-pnpm PR for exact transitive package version drift across yarn.lock, pnpm-lock.yaml, package-manager list output, and node_modules. Triggers include "yarn classic to pnpm", "pnpm migration", "Yarnからpnpm移行", "既存Yarn repoをpnpm化", "lockfile drift", "孫パッケージのバージョン一致", and "pnpm importで一致するか確認".
metadata:
  short-description: Audit Yarn Classic -> pnpm dependency drift
---

# Yarn Classic -> pnpm Migration

This skill migrates an existing Yarn Classic 1.x repo/subdir to pnpm, then verifies whether every transitive package version was preserved. If not, it makes every drift visible and reviewable.

Use the bundled verifier during the migration; do not rely on intuition, `pnpm import`, or passing tests as proof.

## Core Rule

The acceptable outcomes are only:

1. Prove exact `(package name, version)` equality through grandchildren and deeper packages, or
2. Show every mismatch, classify it, and identify the small set that needs runtime monitoring.

In real pnpm migrations, outcome 2 is common. Say "complete match" only if the script proves it.

## Inputs

The user should provide one or more Yarn Classic project roots. Each root is a directory containing `package.json` and usually `yarn.lock`.

Examples:

```text
.
server
global-app
global-app/server
```

If the user names a repo root and it contains nested Yarn lockfile units, discover them with:

```bash
find <repo> -path '*/node_modules' -prune -o -name yarn.lock -print
```

Treat each `yarn.lock` directory as an independent migration unit unless the repo already has a workspace design that says otherwise.

## Migration Workflow

For each Yarn Classic project root:

1. Inspect current state:

```bash
git status --short
sed -n '1,220p' <root>/package.json
test -f <root>/.npmrc && sed -n '1,120p' <root>/.npmrc || true
```

2. Validate the existing Yarn lockfile before changing anything:

```bash
COREPACK_ENABLE_PROJECT_SPEC=0 yarn --cwd <root> install --frozen-lockfile --no-progress
COREPACK_ENABLE_PROJECT_SPEC=0 yarn --cwd <root> check --integrity
COREPACK_ENABLE_PROJECT_SPEC=0 yarn --cwd <root> check --verify-tree
```

If `check --verify-tree` fails because of an existing `resolutions` override, record it. Do not mislabel it as pnpm drift.

3. Pin pnpm metadata in `package.json`:

```json
"packageManager": "pnpm@<current-approved-version>",
"volta": {
  "node": "<existing-node-version>",
  "pnpm": "<same-pnpm-version>"
}
```

Keep existing Node version policy. Do not invent a new Node upgrade unless requested.

4. Convert Yarn `resolutions` to pnpm overrides:

```json
"pnpm": {
  "overrides": {
    "strip-ansi": "6.0.1"
  }
}
```

Remove `resolutions` only after its equivalent is represented under `pnpm.overrides`.

5. Add or update `.npmrc` in the project root. For Yarn Classic compatibility migrations, prefer:

```ini
auto-install-peers=true
strict-peer-dependencies=false
node-linker=hoisted
```

If supply-chain hardening is required by the repo, add the repo's approved age gate. Example:

```ini
minimumReleaseAge=10080
min-release-age=7
```

6. Generate `pnpm-lock.yaml` from `yarn.lock`:

```bash
pnpm --dir <root> import
```

Then run:

```bash
pnpm --dir <root> install --lockfile-only
```

If `pnpm import` is unavailable or fails, record the failure and use `pnpm install --lockfile-only` as fallback. Still perform the drift audit.

7. Remove `yarn.lock` only after `pnpm-lock.yaml` exists:

```bash
git rm <root>/yarn.lock
```

If this is a shared repo with multiple lockfile units, remove only the lockfile for the unit being migrated.

8. Rewrite package manager commands in owned config:

- `yarn install --frozen-lockfile` -> `pnpm install --frozen-lockfile --ignore-scripts`
- `yarn --cwd <root> <cmd>` -> `pnpm --dir <root> <cmd>` or `pnpm -C <root> <cmd>`
- `yarn build` / `yarn test` -> `pnpm run build` / `pnpm test` as appropriate
- GitHub Actions cache: `cache: yarn` -> `cache: pnpm`; lock path to `pnpm-lock.yaml`
- Docker/CI install should include `--ignore-scripts` unless the repo explicitly needs install scripts.

Search targets:

```bash
rg -n "yarn|yarn.lock|cache: 'yarn'|cache: yarn|--frozen-lockfile" .github Dockerfile '*Dockerfile' vercel.json netlify.toml render.yaml railway.toml railway.json package.json README.md AGENTS.md
```

9. Run local verification using pnpm:

```bash
pnpm --dir <root> install --frozen-lockfile --ignore-scripts
pnpm --dir <root> run generate   # if present
pnpm --dir <root> run typecheck  # if present
pnpm --dir <root> test           # if present
```

Do not run repository-prohibited commands such as Prisma migrations if local project instructions forbid them.

10. Run the drift audit below and write a report before claiming the migration is safe.

## Bundled Verifier

Run the script from this skill directory:

```bash
SKILL_DIR="${HOME}/.agents/skills/yarn-classic-to-pnpm"
python3 "$SKILL_DIR/scripts/verify-pnpm-migration-versions.py" --help
```

The script has no third-party dependencies.

Modes:

```bash
# One lockfile pair, full details
python3 "$SKILL_DIR/scripts/verify-pnpm-migration-versions.py" lock <yarn.lock> <pnpm-lock.yaml>

# One installed node_modules pair, full details
python3 "$SKILL_DIR/scripts/verify-pnpm-migration-versions.py" node-modules <yarn_node_modules> <pnpm_node_modules>

# One yarn list / pnpm list pair, full details
python3 "$SKILL_DIR/scripts/verify-pnpm-migration-versions.py" list-json <yarn_list.jsonl> <pnpm_list.json>

# Standard 3-subdir summary table for repos shaped like:
# server/, global-app/server/, global-app/
python3 "$SKILL_DIR/scripts/verify-pnpm-migration-versions.py" all-locks \
  --yarn-root /private/tmp/yarn-modules \
  --pnpm-root .
python3 "$SKILL_DIR/scripts/verify-pnpm-migration-versions.py" all-node-modules \
  --yarn-root /private/tmp/yarn-modules \
  --pnpm-root .
```

`all-*` commands exit 0 by default for human review. Add `--fail-on-drift` for CI-style failure.

## Workflow

1. Identify every Yarn Classic lockfile unit in the PR. Common examples: `server/`, `global-app/`, `global-app/server/`.
2. Create or reuse a clean worktree at the pre-migration branch:

```bash
git worktree add /private/tmp/yarn-modules develop
```

3. Install Yarn Classic dependencies in that worktree:

```bash
COREPACK_ENABLE_PROJECT_SPEC=0 yarn --cwd /private/tmp/yarn-modules/server install --frozen-lockfile --no-progress
COREPACK_ENABLE_PROJECT_SPEC=0 yarn --cwd /private/tmp/yarn-modules/global-app/server install --frozen-lockfile --no-progress
COREPACK_ENABLE_PROJECT_SPEC=0 yarn --cwd /private/tmp/yarn-modules/global-app install --frozen-lockfile --no-progress
```

4. Confirm Yarn's own integrity if the review needs to prove the old lockfile was valid:

```bash
COREPACK_ENABLE_PROJECT_SPEC=0 yarn --cwd <subdir> check --integrity
COREPACK_ENABLE_PROJECT_SPEC=0 yarn --cwd <subdir> check --verify-tree
```

5. Run `all-locks` for the primary evidence.
6. Run `all-node-modules` for local runtime reality.
7. Optionally run package-manager list comparison as an independent estimate:

```bash
COREPACK_ENABLE_PROJECT_SPEC=0 yarn --cwd /private/tmp/yarn-modules/server list --json --depth=999 > /tmp/server_yarn_list.jsonl
pnpm --dir server list --json --depth Infinity > /tmp/server_pnpm_list.json
python3 "$SKILL_DIR/scripts/verify-pnpm-migration-versions.py" list-json /tmp/server_yarn_list.jsonl /tmp/server_pnpm_list.json
```

8. Interpret and report the remaining drift. Do not hide the raw counts.

## Reading Output

The detailed output uses these fields:

- `status=VERSION_SET_CHANGED`: same package name remains, but the version set changed.
- `status=MAJOR_COLLAPSED`: same package name remains, but a Yarn-side major line is absent in pnpm. Treat as `CHECK_REQUIRED`.
- `status=MISSING_NAME`: package name itself is absent in pnpm. Treat as `CHECK_REQUIRED`.
- `missing_yarn_version`: the exact Yarn-side `(name, version)` not present in pnpm.
- `all_yarn_versions`: every Yarn-side version for that package name.
- `all_pnpm_versions`: every pnpm-side version for that package name.
- `ALIAS_TO`: likely npm alias notation difference; verify the real package exists in pnpm before accepting it.

Example interpretation:

```text
zod : status=MAJOR_COLLAPSED  missing_yarn_version=4.3.6  all_yarn_versions=3.25.67/4.3.6  all_pnpm_versions=3.25.67  risk=CHECK_REQUIRED
```

This means `zod` still exists, but the Yarn-side `zod@4.x` line disappeared. It may be semver-legal if the depender accepts `^3.25 || ^4`, but it is not "nothing"; it is a runtime review item.

## Risk Triage

Use this order:

1. `MISSING_NAME` in production dependency paths: highest priority.
2. `MAJOR_COLLAPSED` in production dependency paths: high priority.
3. Runtime dependency patch/minor changes: smoke-test target.
4. Monitoring/tracing dependencies such as `@opentelemetry/*`: verify observability, usually lower app-function risk.
5. `@grpc/proto-loader` / Firebase Admin / Firestore path patch changes: smoke-test DB/Firebase paths.
6. OS optional binaries like `@esbuild/<os>-<arch>` and `@rollup/<os>-<arch>`: usually build/runtime-environment dependent, not app logic.
7. Dev/build/test tooling such as `esbuild`, `rollup`, `@typescript-eslint/*`, `@jridgewell/*`: rely on typecheck/test/build-style gates, but still list them.
8. npm alias differences: accept only when `ALIAS_TO real@version` is present and the real package exists on pnpm side.

For Test Maker's observed migration, the practical conclusion was:

- Complete equality was false.
- Most drift was optional OS binaries, dev/build tooling, patch/minor consolidation, or Yarn duplicate-version collapse.
- Strong runtime watch item: `server/` `zod` major collapse through `@modelcontextprotocol/sdk` / `zod-to-json-schema`.
- Light smoke items: `@opentelemetry/*` for Sentry tracing, `@grpc/proto-loader` for Firebase/Admin/Firestore path.

## `pnpm import` Guidance

`pnpm import` is useful and should generally be tried early, but do not claim it proves equality.

Reasons:

- pnpm and Yarn Classic model peer dependencies and optional dependencies differently.
- Adding `pnpm.overrides`, changing `.npmrc`, or reinstalling after import can re-resolve transitive packages.
- The final `pnpm-lock.yaml` must still be compared mechanically against the old `yarn.lock`.

If a PR did not use `pnpm import`, you may create a throwaway branch/worktree and try it as a counterfactual. Still judge by verifier output, not by import intent.

## Report Template

Use this shape in PR descriptions or initiative reports:

```md
## Yarn -> pnpm dependency drift audit

Conclusion:
- Exact transitive version equality: NO
- All drift mechanically visible: YES
- Runtime watch items: <short list>

Primary lockfile comparison:
<paste all-locks table>

Local node_modules comparison:
<paste all-node-modules table>

Interpretation:
- Most drift is <optional OS binaries / dev tooling / patch-minor consolidation / Yarn duplicate-version collapse>.
- Strong check required:
  - <package>: <why, path, command used to verify>
- Light smoke:
  - <package group>: <scope>

Reproduction:
<commands another terminal can run>
```

## Completion Checklist

Before saying the migration audit is done:

- A pre-migration Yarn worktree exists or old `yarn.lock` files were extracted from the target branch.
- `yarn install --frozen-lockfile` succeeded for every Yarn lockfile unit being compared.
- `all-locks` or equivalent per-lock `lock` commands were run.
- `node-modules` or `all-node-modules` was run if local installed reality matters.
- If `list-json` is used, `yarn_only` counts match lockfile comparison, or the discrepancy is explained.
- Every `MISSING_NAME` and `MAJOR_COLLAPSED` production-path item has an explicit interpretation.
- The user gets exact reproduction commands.
