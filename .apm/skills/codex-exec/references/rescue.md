# Rescue Template

Codex に診断・修正・実装を任せるときのプロンプト雛形。`codex-exec` の `rescue` モードで使う。

## サンドボックス前提

- `--sandbox workspace-write` + `--ask-for-approval never`
- Codex が自律的にファイル編集を行う
- 変更スコープを `<action_safety>` で縛る

## 基本テンプレ（Diagnosis + Fix）

```xml
<task>
{{USER_REQUEST}}
対象リポジトリ: {{REPO_HINT}}
関連する失敗文脈やエラー: {{FAILURE_CONTEXT}}
</task>

<default_follow_through_policy>
Default to the most reasonable low-risk interpretation and keep going.
Only stop to ask questions when a missing detail changes correctness, safety, or an irreversible action.
</default_follow_through_policy>

<completeness_contract>
Resolve the task fully before stopping.
Apply the fix, do not just describe it.
Check for follow-on fixes, edge cases, and cleanup required for a correct result.
</completeness_contract>

<verification_loop>
Before finalizing, verify the change by re-reading the edited files and running the smallest relevant check available (type check, unit test, lint) to confirm the fix is coherent.
</verification_loop>

<missing_context_gating>
Do not guess missing repository facts.
If a required detail is absent, retrieve it with tools or stop and state exactly what remains unknown.
</missing_context_gating>

<action_safety>
Keep changes tightly scoped to the stated task.
Avoid unrelated refactors, renames, or style-only cleanup.
Call out any risky or irreversible action before taking it.
</action_safety>

<structured_output_contract>
At the end, return:
1. summary of the fix
2. touched files
3. verification performed
4. residual risks or follow-ups
</structured_output_contract>
```

## 診断のみ（Diagnosis-only）

ユーザーが「調べるだけ」「原因だけ知りたい」と言っているとき。
サンドボックスは `--sandbox read-only` に切り替える。

```xml
<task>
Diagnose why {{SYMPTOM}} is happening in this repository.
Use available repository context and tools to identify the most likely root cause.
Do not apply any fix. Do not modify files.
</task>

<compact_output_contract>
Return:
1. most likely root cause
2. supporting evidence (file:line, log, observed behavior)
3. smallest safe next step to confirm or fix
</compact_output_contract>

<default_follow_through_policy>
Keep going until you have enough evidence to identify the root cause confidently.
Only stop to ask questions when a missing detail changes correctness materially.
</default_follow_through_policy>

<verification_loop>
Before finalizing, verify that the proposed root cause matches the observed evidence.
</verification_loop>

<missing_context_gating>
Do not guess missing repository facts.
If required context is absent, state exactly what remains unknown.
</missing_context_gating>
```

## 実装タスク（New Feature / Refactor）

新規機能・リファクタのときはこちら。

```xml
<task>
Implement the following in this repository:
{{USER_REQUEST}}

Constraints:
- {{CONSTRAINT_1}}
- {{CONSTRAINT_2}}
</task>

<default_follow_through_policy>
Default to the most reasonable low-risk interpretation and keep going.
</default_follow_through_policy>

<completeness_contract>
Resolve the task fully before stopping.
Ensure the implementation compiles / type-checks cleanly.
Check for edge cases implied by the task and handle them.
</completeness_contract>

<verification_loop>
Before finalizing, verify the implementation by:
- re-reading the touched files for coherence
- running the smallest relevant check (type check, lint, unit test) if available
</verification_loop>

<action_safety>
Keep changes tightly scoped.
Avoid unrelated refactors or renames.
</action_safety>

<structured_output_contract>
At the end, return:
1. summary of the implementation
2. touched files
3. verification performed
4. assumptions made
5. follow-ups not handled
</structured_output_contract>
```

## Resume 時

`codex exec resume --last` で呼び出すとき、本文には **追加指示のみ** を書く。
既に前回のコンテキストは保持されている。

```xml
<task>
{{DELTA_INSTRUCTION}}
</task>
```

前回と方針が変わったときだけ、変わった方針を明示する。
