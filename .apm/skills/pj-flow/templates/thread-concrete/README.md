# thread-concrete 雛形

**情報収集・仕様具体化系**のThread用雛形。
purposeは `concrete`（起点）/ `reconcrete`（前提変更での再仕様化）/ `spike`（技術検証）など、情報収集が主眼のThreadで使う。

## 使い方（pj-flow スキル経由）

```bash
SLUG=<your-slug>
PURPOSE=concrete   # or reconcrete, spike など
TS=$(TZ=Asia/Tokyo date +%Y%m%d%H%M)
REPO_ROOT=$(git rev-parse --show-toplevel)
PROJECTS_ROOT="${PROJECTS_ROOT:-$REPO_ROOT/.claude/my-projects}"
SKILL_DIR=<pj-flow-skill-dir>
cp -r "$SKILL_DIR/templates/thread-concrete" \
      "$PROJECTS_ROOT/$SLUG/threads/${TS}-${PURPOSE}"
```

## ファイル構成

- `OBJECTIVE.md` — 開始時。参照Thread(s) / 上書き対象 / 調査観点 / Done定義
- `OUTPUT.md` — 終了時。詳細仕様 / 判断根拠 / Open Questions / 長期記憶の更新状況
- `<assets...>` — 調査成果物（スクショ、CSV、SQL結果、メモ）はフォルダ直下に自由配置

## 起点 concrete の役割

Projectの**起点**は concrete から始めるのが基本。施策草案・背景情報を受け、コードベース・Issue・Git履歴・DB・実データ等を使って仕様を具体化する。

## 再concrete / spike の役割

implementation中に前提が覆ったり、別の技術検証が必要になった場合に追加で立てるThread。OBJECTIVE冒頭で **上書き対象の旧Thread** を明示し、旧OUTPUT.mdがなぜ古くなったかを記述する。旧OUTPUT.mdは削除しない。

## このThreadでやらないこと

- 実装コードを書く（検証用の小スニペットは例外）
- PRを作る
- 仕様が未決定の部分を曖昧に放置（必ず Open Questions として列挙）
