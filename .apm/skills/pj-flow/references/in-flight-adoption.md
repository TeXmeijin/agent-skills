# in-flight-adoption — 途中昇格 / 途中合流

会話途中で「これ実はPJ管理下に置きたい」「これ既存PJの作業だった」と気づいたケースの処理。

## 2パターン

### A. **In-flight adoption**（新規PJに昇格）
スレッドで雑談ベースに進んでいた作業が、規模・複雑さからPJとして管理した方がよくなったケース。
→ 空PJを初期化 + 会話内容から事後Threadを起こす。

### B. **In-flight join**（既存PJに合流）
スレッドの作業が、実は既存PJの一環だったと気づいたケース。
→ 既存PJに新Threadを切る + 会話内容から事後OUTPUTを起こす。

---

## A. In-flight adoption の手順

1. **slug 候補を提示してAskUserQuestion**（2案 + Other）
2. **`<slug>/CLAUDE.md` を初期化**（pj-flow テンプレ）
3. **frontmatter を会話から埋める**
   - `branch`: 現在のブランチ（`git branch --show-current`）
   - `issue_url`: あれば。なければ `null`
   - `bundled_repos`: 触ったリポから推定
   - `created_at`: 会話の最初の発言日 or 今日
4. **本文を会話から起こす**
   - 「施策概要」: 「ユーザーが何をしたかったか」を1〜2段落で
   - 「背景」: 会話冒頭の動機
   - 「スコープ」「非スコープ」: 会話で実際に触れた範囲 / 触れていないが関連する範囲
5. **起点Thread を生成**
   - 主に**コード変更があったか**で系統判定:
     - コード変更あり → `<TS>-implementation`
     - 調査・議論のみ → `<TS>-concrete`
   - 注記: 冒頭1行に `> このThreadは in-flight adoption により事後生成された`
6. **OBJECTIVE.md / OUTPUT.md を会話から事後記入**
   - OBJECTIVE: 「このThreadの目的」「Done定義」
   - OUTPUT: 「実装サマリ」「変更ファイル一覧」「判断根拠の事実」「Open Questions」
7. **ユーザーに「この内容で確定か」を確認**

### Open Questions の扱い

会話途中ということは、まだ未決定の論点が残っている可能性が高い。
**未決定なものは必ず Open Questions に拾い上げる**。後で別Threadで解決する。

---

## B. In-flight join の手順

1. **既存 `<slug>/CLAUDE.md` を読む**
2. **現スコープと矛盾しないか確認**
   - 矛盾しない → そのまま join
   - 矛盾する → 仕様変更インパクト判定（小/中/大）。大なら `reconcrete` Thread を立てる方が正しい
3. **新Threadを切る**（系統判定は A と同じ）
4. **OBJECTIVE.md「参照Thread(s)」に既存Threadを明示**
   - 「直前Thread」を自動採用しない。会話の成果が**どのThreadの続きなのか**をユーザーに確認
5. **OUTPUT.md を会話から事後記入**（A と同じ）
6. **長期記憶の更新が必要なら `<slug>/CLAUDE.md` を上書き + `updated_at` 更新**

---

## 共通の注意

- **事後Thread であることを必ず明記**（冒頭注記）。後で読み返したときに「リアルタイムで書かれた Thread」と区別できるように
- **会話の長さに応じて要約レベルを調整**:
  - 短い会話（〜数千 token）→ 全部移植
  - 長い会話（数万 token〜）→ 要点だけ。詳細は「会話履歴は本Threadフォルダ内 `chat-log.md` に保存」として別ファイルに逃がす
- **adoption / join の判断は ユーザー主導**。スキル側から勝手に「これPJ化すべき」と推奨しない（会話の自然な流れを邪魔する）

---

## チャットログ保存（オプション）

会話履歴を残したい場合:

```bash
SLUG=<your-slug>
TS=<TS>
PURPOSE=<purpose>
PROJECTS_ROOT="${PROJECTS_ROOT:-$(git rev-parse --show-toplevel)/.claude/my-projects}"
mkdir -p "$PROJECTS_ROOT/$SLUG/threads/${TS}-${PURPOSE}"
# 会話ログを手動 / pbpaste で chat-log.md に保存
pbpaste > "$PROJECTS_ROOT/$SLUG/threads/${TS}-${PURPOSE}/chat-log.md"
```

ただし**コミットすべきかは要確認**。チャットログには内部議論・人名・センシティブな情報が混ざる可能性。
