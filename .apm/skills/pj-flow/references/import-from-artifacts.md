# import-from-artifacts — 外部成果物（PR / Draft PR / Issue / merged PR / コード）からPJ逆生成

「このPRからIn Progress PJ作って」「Issueから起こして」のシナリオ。**既に作業がある程度進んでいるのにPJ管理に乗っていない**状態を、後追いでpj-flow化する。

## 入力パターン

| 入力 | 推定される状態 | 推奨初期Thread |
|---|---|---|
| **Issue のみ**（コードまだ） | 仕様検討段階 | `<TS>-concrete` を空に近い状態で生成 |
| **Draft PR**（コードあり / レビュー前） | 実装着手済み・完了前 | `<TS>-implementation`（事後）+ 必要なら `<TS>-concrete`（事後） |
| **Open PR**（レビュー中） | 実装完了・マージ前 | `<TS>-implementation`（事後）。`status: in_progress` |
| **Merged PR** | 既にリリース済み | `status: closed` で逆生成。`closed_at` 入れる |
| **branch + commits**（PRもIssueもなし） | 個人開発の途中 | `<TS>-implementation`（事後）。`issue_url: null` |

## 手順

### 1. 入力の収集

`gh` / Linear MCP / git をフル活用して、以下を集める:

```bash
# PR から
gh pr view <pr-url> --json title,body,headRefName,baseRefName,state,isDraft,labels,assignees,createdAt,mergedAt,url,commits,files

# Issue から
gh issue view <issue-url> --json title,body,labels,assignees,state,createdAt,closedAt,url
# Linear なら mcp__linear__get_issue

# branch から diff サマリ
git fetch origin <branch>
git log origin/<base>...origin/<branch> --oneline
git diff --stat origin/<base>...origin/<branch>
```

これらを**会話に貼って整理**してから新PJを起こす。

### 2. slug の決定

PR / Issue のタイトルから kebab 化候補を2案出してユーザーに選ばせる。

```
例: "[NOS-6124] AI先生検索の精度改善" → ai-teacher-search-accuracy / nos-6124-search-accuracy
```

候補2案 + 「Other」で AskUserQuestion。

### 3. 長期記憶（`<slug>/CLAUDE.md`）の生成

| 旧情報 | 新フィールド |
|---|---|
| PR title | 本文タイトル `# <Project Title>` |
| Issue body の「背景」 | 「## 背景」 |
| PR body の「概要」 | 「## 施策概要」 |
| PR の変更ファイル群 | 「## 現在のスコープ」（推定。要確認） |
| Issue の「やらないこと」 | 「## 非スコープ」 |
| PR url / Issue url | frontmatter `pr_url` / `issue_url` |
| PR の headRef | frontmatter `branch` |
| 変更ファイル群の repo 種別 | frontmatter `bundled_repos` |
| PR createdAt / mergedAt | frontmatter `created_at` / `closed_at` |
| PR state | frontmatter `status` (`open` → `in_progress`, `merged` → `closed`) |

**推定箇所には `# TODO: confirm` コメントを残し**、ユーザー確認を促す。

### 4. Thread の事後生成

**入力パターンで分岐**:

#### Pattern A: Issue のみ
```bash
TS=$(TZ=Asia/Tokyo date +%Y%m%d%H%M)
SKILL_DIR=<pj-flow-skill-dir>
cp -r "$SKILL_DIR/templates/thread-concrete" \
      "$PROJECTS_ROOT/$SLUG/threads/${TS}-concrete"
```
OBJECTIVE.md の「このThreadの目的」「調査観点」を Issue body から起こす。OUTPUT.md は空のまま（次のセッションで埋める）。

#### Pattern B: Draft / Open PR
```bash
TS=$(TZ=Asia/Tokyo date +%Y%m%d%H%M)
SKILL_DIR=<pj-flow-skill-dir>
cp -r "$SKILL_DIR/templates/thread-implementation" \
      "$PROJECTS_ROOT/$SLUG/threads/${TS}-implementation"
```
OUTPUT.md の「実装サマリ」「変更ファイル一覧」「PR状況」を **PR から逆生成**:
- `gh pr view --json files` で得た変更ファイル群をリポ別に分類
- 「検証結果」は PR の CI ステータスから（pass/failing/未実行）
- 冒頭注記: `> このThreadはimport-from-artifactsにより事後生成された`

#### Pattern C: Merged PR
Pattern B と同じだが `<slug>/CLAUDE.md` frontmatter で:
- `status: closed`
- `closed_at: <merged_at の日付>`
- `pr_url: <pr url>`

「PJをそもそも管理下に置く意味があるか」は要確認（過去PJを後追いで作っても活用機会が少ない可能性）。

#### Pattern D: branch + commits のみ
Pattern B と同じだが `issue_url: null` `pr_url: null`。コミットメッセージ群から実装サマリを起こす。

### 5. Open Questions の抽出

逆生成時、**推定で埋めた箇所**は必ず Open Questions に明示:

```markdown
## Open Questions

- [ ] このPJの「## 現在のスコープ」は PR の変更ファイル群から推定した。実際の意図と合っているか要確認
- [ ] `bundled_repos` は server/client と推定。他リポも絡むなら追記
- [ ] このPRが対応している Issue / Linear チケットは <url> でよいか
```

### 6. ユーザー確認

「この内容で確定でよいか」を1回確認してから commit する。

## ありがちな失敗

- **PR body をそのまま「施策概要」にコピー**して終わり → PR body は実装サマリに寄っているので、長期記憶の「施策概要」とは粒度が違う。1段抽象を上げる必要あり
- **Thread の `YYYYMMDDHHMM` を「今」にする vs PRの作成日時にする** → デフォルトは「今」（事後生成だが現時点で起こした、という意味で）。「当時の時刻」にしたい場合は明示
- **複数PRに分かれているPJを1Thread に畳む** → PR数 = Thread数 として複数Thread に展開するのが正しい
