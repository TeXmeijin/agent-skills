# Prompt Blocks

Codex / GPT-5 系に渡すプロンプトで使える XML ブロック集。必要なものだけ組み合わせる。

## 原則

- **1 プロンプト 1 タスク**。無関連なジョブを混ぜない。
- **what done looks like を明示**。Codex は推測しない前提で書く。
- **コントラクト > reasoning を上げる**。弱いプロンプトに high effort をかけるより、blocks を足す。
- **XML タグ名は固定**。下記のタグ名を使い回す。
- **必要最小限**。要らないブロックは外す。

## コアブロック

### `<task>`（ほぼ必須）

```xml
<task>
具体的なジョブと、対象リポジトリ／失敗文脈、期待する最終状態を 1-3 文で書く。
</task>
```

### `<structured_output_contract>`

応答の形が重要なとき。

```xml
<structured_output_contract>
Return exactly the requested shape and nothing else.
Keep the answer compact.
Put the highest-value findings or decisions first.
</structured_output_contract>
```

### `<compact_output_contract>`

散文で良いが冗長は嫌なとき。

```xml
<compact_output_contract>
Keep the final answer compact and structured.
Do not include long scene-setting or repeated recap.
</compact_output_contract>
```

## Follow-through

### `<default_follow_through_policy>`

Codex にルーチンな確認で止まらず進んでほしいとき。

```xml
<default_follow_through_policy>
Default to the most reasonable low-risk interpretation and keep going.
Only stop to ask questions when a missing detail changes correctness, safety, or an irreversible action.
</default_follow_through_policy>
```

### `<completeness_contract>`

デバッグ・実装・複数ステップのタスク向け。

```xml
<completeness_contract>
Resolve the task fully before stopping.
Do not stop at the first plausible answer.
Check whether there are follow-on fixes, edge cases, or cleanup needed.
</completeness_contract>
```

### `<verification_loop>`

正しさが要るとき。

```xml
<verification_loop>
Before finalizing, verify the result against the task requirements and the changed files or tool outputs.
If a check fails, revise the answer instead of reporting the first draft.
</verification_loop>
```

## Grounding

### `<missing_context_gating>`

推測されたくないとき。

```xml
<missing_context_gating>
Do not guess missing repository facts.
If required context is absent, retrieve it with tools or state exactly what remains unknown.
</missing_context_gating>
```

### `<grounding_rules>`

レビュー・原因分析など主張の根拠が必要なとき。

```xml
<grounding_rules>
Ground every claim in the provided context or your tool outputs.
Do not present inferences as facts.
If a point is a hypothesis, label it clearly.
</grounding_rules>
```

## Safety

### `<action_safety>`

書き込み系タスク向け。スコープを広げさせない。

```xml
<action_safety>
Keep changes tightly scoped to the stated task.
Avoid unrelated refactors, renames, or cleanup unless required for correctness.
Call out any risky or irreversible action before taking it.
</action_safety>
```

## Review 系

### `<dig_deeper_nudge>`

一つ目の issue で終わらせない。

```xml
<dig_deeper_nudge>
After you find the first plausible issue, check for second-order failures, empty-state behavior, retries, stale state, and rollback paths before you finalize.
</dig_deeper_nudge>
```

## アンチパターン

- **曖昧な task**: 「見てどう思う？」→ `<task>` で具体化。
- **出力コントラクト無し**: 「調べて報告して」→ `<structured_output_contract>` か `<compact_output_contract>` を足す。
- **follow-through 無し**: 「デバッグして」→ `<default_follow_through_policy>` を足す。
- **reasoning を上げて誤魔化す**: 「もっと賢く考えて」→ `<verification_loop>` を足す方が先。
- **複数ジョブ混載**: 「レビューして修正してドキュメントも」→ 別々の run に分割。
- **根拠なき断定要求**: 「なぜ落ちたか正確に教えて」→ `<grounding_rules>` を足す。
