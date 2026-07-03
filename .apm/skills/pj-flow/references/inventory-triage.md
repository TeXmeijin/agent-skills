# 棚卸し（Inventory triage）詳細

全PJを **外部の実データと照合**して状態を最新化するモード（シナリオ#11）。
frontmatter の `status` / `updated_at` は放置で腐るので、棚卸しでは**実データを正**として直す。

新規Threadは原則切らない。frontmatter と本文（現時点スナップショット）の更新が主。
残作業を再開するPJは別途シナリオ#2（再開）へ回す。

---

## 手順

### 1. 棚卸し（収集）

```bash
PROJECTS_ROOT="${PROJECTS_ROOT:-$(git rev-parse --show-toplevel)/.claude/my-projects}"
# in_progress の全PJ
grep -l '^status: in_progress' "$PROJECTS_ROOT"/*/CLAUDE.md | xargs -I{} dirname {}
```

各 `<slug>/CLAUDE.md` の frontmatter から `pr_url` / `branch` / `issue_url` / `updated_at` / `bundled_repos` を読む。

### 2. 実データ照合

frontmatter を鵜呑みにしない。外部の一次データで現況を確認する:

- `pr_url` あり → `gh pr view <url> --json state,mergedAt,title`（`MERGED` か / マージ日）
- `pr_url: null` だが branch あり → `gh pr list --head <branch> --state all --json number,state,url` で実PRを探す
- `issue_url`（Linear）→ Linear MCP の `get_issue` で status 確認
- `issue_url`（GitHub）→ `gh issue view <url> --json state`
- インフラ系（AWS リソース削除待ち等）→ readonly profile で確認できる範囲で実在チェック

**frontmatter と実態がズレていたら実態を正**として frontmatter / 本文を直す。

### 3. 5分類に振り分け

| 分類 | 条件 | アクション |
|---|---|---|
| **A. マージ済みなのに open** | PR が MERGED なのに `status: in_progress` | 実データ確認のうえ `status: closed` / `closed_at` / `updated_at` を当日付与。frontmatter 自体が欠落していれば**新規付与してから** close |
| **B. 稼働中・新規** | PR/Issue が直近で更新、または `created_at` が新しい | **触らない**（対象外と明記） |
| **C. stale だが残作業実在** | しばらく更新がないが、まだやるべき残作業がある | **1件ずつ AskUserQuestion** で「残スコープ / 非スコープ / 次タスク」を確定。確定内容を本文に反映し `in_progress` 維持（または phase 更新） |
| **D. 実質未着手 / productize 済み** | OUTPUT 空で着手痕跡なし、または成果が他（skill 等）に移って参照不要 | `status: archived`、`updated_at` 更新。**削除はしない** |
| **E. 残是正が散在** | 1PJ では収まらない残是正（例: 監査の指摘対応）が複数PJに散らばる | 集約用の **新規 remediation PJ** をシナリオ#2.1 で起こし、各PJの本文から参照させる |

### 4. 不可逆操作は確認を挟む

- B（触らない）と、PR MERGED が明白な A は確認不要で進めてよい。
- **Close / archived 化 / 新規PJ作成** は推測で確定しない。特に C は残作業の解釈が割れるので必ず AskUserQuestion で1件ずつ方針を取る。

### 5. AIが代行できないアクションを最後に列挙

棚卸しで「残っているが AI が実行できない」アクションを漏らさず明示する:

- AWS 書き込み（リソース削除等。readonly profile では不可）
- MFA / credential 操作
- 人手の意思決定が起点になる保留タスク

これらは「棚卸し済み = 完了」と誤認させないよう、サマリの末尾に独立節で出す。

### 6. 最終サマリを表で報告

分類別（A〜E）に件数と各PJの確定方針を表でまとめる。基準日（`YYYY-MM-DD`）を明記する。

---

## frontmatter 更新の具体

- Close: `status: closed` / `closed_at: YYYY-MM-DD` / `updated_at: YYYY-MM-DD`
- Archive: `status: archived` / `updated_at: YYYY-MM-DD`（`closed_at` は付けない）
- C の方針反映: 本文の「現在のスコープ / 非スコープ」を上書き、必要なら `phase` 等の独自フィールドを実態に合わせる
- frontmatter 欠落PJ: §5 の固定スキーマで補完してから分類処理する

旧 OUTPUT.md / 旧 Thread は棚卸しでも**削除しない**。状態変更は frontmatter と本文の上書きで表現し、経緯は git log で追う。
