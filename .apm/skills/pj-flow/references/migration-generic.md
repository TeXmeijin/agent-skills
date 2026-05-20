# migration-generic — 不明な独自PJ管理方式からのマイグレ

ユーザーから「うちの個人開発リポにも独自のPJ管理があるんだけど、pj-flow に揃えたい」と依頼されたときの汎用手順。

## ステップ1: 旧フォーマットを言語化する

ヒアリング（または ls / grep ベースの調査）で以下を埋める:

| 項目 | 例 |
|---|---|
| 旧ロケーション | `docs/initiatives/` / `notes/projects/` / `.notes/` |
| 1PJの単位 | 単一markdown / フォルダ / yaml + 複数md |
| frontmatter 有無 | あり / なし |
| Thread概念 | あり（独自呼称） / なし（PRと1対1） |
| アーカイブ | サブディレクトリ / status field / 別repo |
| 命名規約 | kebab / snake / TS prefix / Linear ID prefix |

## ステップ2: pj-flow との対応マップを作る

ユーザーと一緒に **3列の対応表** を作る:

| 旧概念 | pj-flow概念 | 移行時の操作 |
|---|---|---|
| `docs/initiatives/<slug>.md` (1ファイル) | `<PROJECTS_ROOT>/<slug>/CLAUDE.md` + 1 Thread | 内容分解 |
| `status: active / done` field | frontmatter `status: in_progress / closed` | rename |
| 「メモ」セクション | Thread の OUTPUT「判断根拠」 | 移植 |
| GitHub Issue 番号 | frontmatter `issue_url` | URL化 |

対応が **1:多** や **多:1** になるところは要相談ポイントとしてフラグ。

## ステップ3: 試行 PJ で 1 本通す

いきなり全PJ移行しない。**最も典型的な PJ 1本を選んで pj-flow 形式に変換**し、ユーザーに確認してもらう。

```bash
SLUG=<sample-slug>
PROJECTS_ROOT="${PROJECTS_ROOT:-$(git rev-parse --show-toplevel)/.claude/my-projects}"
SKILL_DIR=<pj-flow-skill-dir>
mkdir -p "$PROJECTS_ROOT/$SLUG/threads"
cp "$SKILL_DIR/templates/project/CLAUDE.md" "$PROJECTS_ROOT/$SLUG/CLAUDE.md"
TS=$(TZ=Asia/Tokyo date +%Y%m%d%H%M)
# Concrete系 / Implementation系を旧PJの中身から判断
cp -r "$SKILL_DIR/templates/thread-concrete" "$PROJECTS_ROOT/$SLUG/threads/${TS}-concrete"
```

その後、旧データを Claude に**手で埋めさせる**。差分が見えたらヒアリングしてマップを微調整。

## ステップ4: 残りの PJ を順次変換

ステップ3で確定したマップに従って一気に変換する。1コミット=1PJ。

## 引っかかりがちなポイント

- **複数Threadに分けるべきか1Threadに畳むべきか**: 旧PJに「設計→実装→修正」の経緯が明確に分かれて記録されていれば複数Threadに分割。一気書きされていれば1Threadに畳む。
- **Open Questions の発掘**: 旧PJに「TODO」「??」「未決定」のキーワードが残っていたら Open Questions に拾い上げる。
- **アーカイブ済みPJの優先度**: ふつう低い。塩漬けでよい。
- **landing 等 pj-flow に無い概念**: 失わずに `<slug>/CLAUDE.md` の「## 参考」に1行残す。後で議論できる。
