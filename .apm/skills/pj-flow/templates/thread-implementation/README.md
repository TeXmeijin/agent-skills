# thread-implementation 雛形

**実装系**のThread用雛形。purposeは `implementation` / `pivot` / `fix` など。

## 使い方（pj-flow スキル経由）

```bash
SLUG=<your-slug>
PURPOSE=implementation   # or pivot, fix など
TS=$(TZ=Asia/Tokyo date +%Y%m%d%H%M)
REPO_ROOT=$(git rev-parse --show-toplevel)
PROJECTS_ROOT="${PROJECTS_ROOT:-$REPO_ROOT/.claude/my-projects}"
SKILL_DIR=<pj-flow-skill-dir>
cp -r "$SKILL_DIR/templates/thread-implementation" \
      "$PROJECTS_ROOT/$SLUG/threads/${TS}-${PURPOSE}"
```

## 前提

- 参照Thread(s)（多くは直近のconcrete/reconcrete）のOUTPUT.mdが存在し、本Threadの実装範囲が明確になっている
- ただし **「前提がFix済み」とは限らない**。実装中に仕様変更が発生するのはふつう。インパクトに応じて OUTPUT.md の「実装中に発覚した仕様変更」欄に記録する

## ファイル構成

- `OBJECTIVE.md` — 参照Thread / 前提の扱い / 対象範囲 / 実装タスク / Done定義 / Non-Goal
- `OUTPUT.md` — 実装サマリ / 変更ファイル / 検証結果 / 仕様変更記録 / PR状況 / 残作業
- `<assets...>` — 動作確認スクショ、実行ログ、PoC結果 等

## 仕様変更が発生したら

- 小（挙動の微調整等）: 現Thread内で吸収。OUTPUT.mdに記録
- 中（設計変更等）: 次 implementation ThreadのOBJECTIVEに変更理由を明記。長期記憶も更新
- 大（前提が覆る）: 本Threadは一旦止め、`reconcrete` Threadを先に立てる

## このThreadの責務

- 実装を完了させ PR 対象ブランチに push する
- 静的チェック / テスト / ローカル動作確認 まで終わらせる
- 残作業と仕様変更は OUTPUT.md に明記
