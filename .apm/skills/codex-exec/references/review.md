# Review Template

Codex にローカル git の差分をレビューさせるときのプロンプト雛形。`codex-exec` の `review` モードで使う。

## サンドボックス前提

- `--sandbox read-only` + `--ask-for-approval never`
- Codex はファイルを編集しない。読んで指摘を返すだけ。

## スコープ選択

ユーザー引数で決める:
- `--scope auto`（既定）: 未追跡 + staged + unstaged をすべて対象
- `--scope working-tree`: 未追跡 + staged + unstaged
- `--scope branch [--base <ref>]`: `<base>...HEAD` の差分

呼び出し前に以下でスコープ把握:

```bash
git status --short --untracked-files=all
git diff --shortstat --cached
git diff --shortstat
# ブランチ指定時
git diff --shortstat <base>...HEAD
```

## 基本テンプレ

```xml
<role>
You are Codex performing a focused code review of local git changes.
</role>

<task>
Review the provided repository changes for material correctness and regression risks.
Target scope: {{TARGET_LABEL}}
</task>

<review_method>
Read the changed files and the surrounding call sites needed to judge correctness.
Prefer depth on a few high-value concerns over breadth of superficial nits.
</review_method>

<finding_bar>
Report only material findings. A material finding affects correctness, regression risk, security, data integrity, or user-facing behavior.
Do not include style feedback, naming feedback, or speculative concerns without evidence.
Each finding must answer:
1. What can go wrong?
2. Why is this code path vulnerable?
3. What is the likely impact?
4. What concrete change would reduce the risk?
</finding_bar>

<dig_deeper_nudge>
After you find the first plausible issue, check for second-order failures, empty-state behavior, retries, stale state, and rollback paths before you finalize.
</dig_deeper_nudge>

<grounding_rules>
Ground every finding in the changed code or the repository context you read.
Do not invent files, lines, or behavior you cannot support.
If a conclusion depends on an inference, label it clearly and keep confidence honest.
</grounding_rules>

<structured_output_contract>
Return a markdown report with:
1. One-line verdict: `approve` or `needs-attention`
2. Findings list, ordered by severity. Each finding:
   - file:line_start-line_end
   - severity (high / medium / low)
   - what can go wrong
   - evidence
   - concrete recommendation
3. If no material finding: say so directly and stop.
</structured_output_contract>

<verification_loop>
Before finalizing, check that each finding is material, tied to a concrete code location, and actionable.
</verification_loop>

<repository_context>
{{GIT_SUMMARY}}

{{GIT_DIFF_OR_FILE_LIST}}
</repository_context>
```

## プロンプトに載せる repository_context

以下を順に連結する:

1. `git status --short --untracked-files=all` の出力
2. `git diff --stat` または `git diff --stat <base>...HEAD` の出力
3. 可能なら `git diff` または `git diff <base>...HEAD` 全文（大きすぎるときは Codex 自身に `git diff` を叩かせる方針で、ファイルパスリストのみ渡す）

極端に大きい差分なら `<repository_context>` は短くし、Codex に tools で探索させる。

## 引数処理

- `--base <ref>`: ブランチ比較のベース指定
- `--scope auto|working-tree|branch`: スコープ
- focus テキスト: 追加の注目点（例: "認証周り重点的に"）

focus テキストがあるときは `<task>` に `User focus: {{USER_FOCUS}}` を添える。
