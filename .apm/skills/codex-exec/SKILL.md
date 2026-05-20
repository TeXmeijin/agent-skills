---
name: codex-exec
description: Codex CLI (codex exec) を直接呼び出して rescue（診断・修正）、review（差分レビュー）、adversarial-review（敵対的レビュー）のいずれかを実行する。ユーザーが明示的に /codex-exec、codex-exec、「codex に投げて」「codex でレビュー」「codex rescue」等と呼んだときだけ発動する。会話コンテキストに codex 的ニュアンスが出ただけでは自動起動しない。
disable-model-invocation: true
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion
---

# codex-exec

Claude Code から OpenAI Codex CLI (`codex exec`) に作業を委譲するための薄いラッパースキル。
内部で node スクリプトを噛ませず、素直に `codex exec` を子プロセス起動する。

## 発動ポリシー

- ユーザーが明示的にこのスキルを名指ししたときだけ動く。
- 「codex」「Codex に投げて」「codex rescue」「codex review」「厳しくレビュー」等の直接指示がトリガー。
- 会話コンテキストで "これ難しい" 等が出ただけでは起動しない。

## 実行手順

### 1. モード判定

ユーザーの発話と引数から次のいずれかに振り分ける。曖昧なら `AskUserQuestion` で1回だけ確認する。

| Mode | トリガー語の例 | サンドボックス | テンプレ |
|---|---|---|---|
| `rescue` | rescue / fix / debug / 詰まった / 助けて / 実装して | `workspace-write` + `never` | [references/rescue.md](references/rescue.md) |
| `review` | review / レビュー / 差分見て | `read-only` + `never` | [references/review.md](references/review.md) |
| `adversarial-review` | 厳しくレビュー / 敵対的 / 叩いて / adversarial | `read-only` + `never` | [references/adversarial-review.md](references/adversarial-review.md) |

### 2. レビュー系はスコープ見積もり

`review` / `adversarial-review` のときは、プロンプト組立前に対象範囲を把握する:

```bash
git status --short --untracked-files=all
git diff --shortstat --cached
git diff --shortstat
```

ベースブランチ指定時は `git diff --shortstat <base>...HEAD` も見る。
サイズ感はそのままプロンプトに添える。

### 3. 松竹梅選択

`AskUserQuestion` を **1 回だけ** 使い、Model × Effort を選ばせる。推奨はタスク性質に応じて先頭にする:

| ランク | label | Model | Effort | 想定用途 |
|---|---|---|---|---|
| 🥇 松 | `松: gpt-5.4 + xhigh` | `gpt-5.4` | `xhigh` | 最難関。設計判断・複雑バグ・高品質レビュー |
| 🥈 竹 | `竹: gpt-5.3-codex + high` | `gpt-5.3-codex` | `high` | 通常コーディング・標準レビュー |
| 🥉 梅 | `梅: gpt-5.4 + medium` | `gpt-5.4` | `medium` | 軽い相談・速い反復 |

推奨のデフォルト:
- `rescue` で「難しい」「詰まった」「根本原因」系 → 松を先頭
- `rescue` で小さな修正 → 梅を先頭
- `review` → 竹を先頭
- `adversarial-review` → 松を先頭

### 4. プロンプト組立

該当テンプレ（references/*.md）を読み、XML ブロックを埋める。

- `<task>`: ユーザーの依頼を 1-3 文で具体化
- レビュー系は `<repository_context>` に git サマリ/diff 出力を貼る
- 追加の focus テキストがあれば `<user_focus>` に入れる
- 冗長なブロックは外す（[references/prompt-blocks.md](references/prompt-blocks.md) の基準に従う）

### 5. Codex 呼び出し

`codex exec` を stdin 経由で叩く（シェルクオート事故を避ける）。

```bash
codex exec \
  --model "<MODEL>" \
  -c model_reasoning_effort="<EFFORT>" \
  --sandbox "<SANDBOX>" \
  --ask-for-approval never \
  -C "$PWD" \
  - <<'PROMPT'
<組み立てたプロンプト本文>
PROMPT
```

- `<MODEL>` / `<EFFORT>` は選択結果で埋める
- `<SANDBOX>`: `rescue` → `workspace-write` / レビュー系 → `read-only`
- `--full-auto` は使わない（挙動を明示したいため）
- 作業ディレクトリは `-C "$PWD"` を明示
- `--output-last-message` は使わない（stdout をそのまま返す）

**フォアグラウンド／バックグラウンド判定**:
- レビューで差分が大きい (`shortstat` で 10 ファイル超 or 500 行超) → `run_in_background: true` を推奨
- rescue で書き込み系・長時間想定 → 推奨 `run_in_background: true`
- それ以外 → フォアグラウンド

### 6. 出力返却

- **Codex の stdout をそのまま返す**。要約・コメント・前置き・後置きを追加しない。
- Codex がエラーで終了した場合のみ、最小限の状況（終了コードと stderr の最後の数行）を返す。
- Codex の指摘した修正をこのスレッドで自分で適用しない。rescue モードで Codex 自身が既に編集済みなら、`git status` で変更を確認するだけにとどめ、別途の編集はしない。

## Codex CLI の前提

- `codex` コマンドが PATH にあり、OpenAI 認証済みであること。
- 未認証時は Codex が認証エラーを吐く。そのときは「`codex login` してください」と伝える。
- Resume 指示（「続き」「さっきの」等）がユーザーから来たら、`codex exec resume --last` を使って同一フラグで呼び出す。PROMPT は追加指示のみを送る（前回分を繰り返さない）。

## やってはいけないこと

- 素の `codex` TUI を起動しない（インタラクティブモードは Claude Code 経由では噛み合わない）。
- `codex exec` 以外のサブコマンドを勝手に使わない（`resume` を除く）。
- プロンプトに冗長な説明を盛らない。[references/prompt-blocks.md](references/prompt-blocks.md) のアンチパターンを参照。
- Model/Effort を勝手に上書きしない。ユーザーが選んだ組を厳守する。
- 「なんとなく codex を呼びたくなった」で起動しない。明示呼び出し時だけ動く。
