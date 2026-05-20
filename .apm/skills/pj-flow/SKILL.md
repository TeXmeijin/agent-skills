---
name: pj-flow
description: PJ管理フロー（長期記憶＋Threadの積み上げ）を任意リポジトリに展開するスキル。デフォルトでは `.claude/my-projects/<slug>/` 配下にProject長期記憶（CLAUDE.md）とThread（OBJECTIVE.md→OUTPUT.md）を積むが、runner / repo 方針に応じて `.agents/my-projects/` 等へカスタム可能。トリガー：「<slug>を再開」「続きやる」「PJ立ち上げ」「新スレッド作って」「OUTPUT書いて」「pbcopyして」「PJクローズ」「このやりとりをPJ管理下に置きたい」「○○PJに合流させたい」「PR/Issueから In Progress PJを作って」「pj-flow にマイグレ」「pj-flow の挙動を直したい」「pjflow」。Claude Code / Codex Agent Skill 両対応。
---

# pj-flow

**長期記憶＋細切れThread**型のPJ管理フローを、任意のリポジトリへ横展開するスキル。
**スキル本体はこの1ファイル**。詳細手順は `references/` に分割。テンプレは `templates/` を `cp -r` して使う。

このスキル自体の所在は runner のスキル配置に従う。典型例:
- Codex / Agent Skills: `~/.agents/skills/pj-flow/`
- Claude Code legacy: `~/.claude/skills/pj-flow`

ユーザーの不満や改善要望はスキル本体（このファイル）を直接 Edit して恒常化する。詳細: `references/self-improvement.md`。

---

## 0. 起動時に最初にやること

スキルが立ち上がった瞬間、**ユーザー意図を以下10種に分類**してから動く。

| # | シナリオ | 代表トリガー |
|---|---|---|
| 1 | **新規PJ立ち上げ** | 「新しいPJ作って」「PJ立ち上げ」「`pj-flow init <slug>`」 |
| 2 | **既存PJ再開** | 「`<slug>` 再開」「`<slug>` の続きやる」「`pj-flow resume <slug>`」 |
| 3 | **Thread切り出し**（既存PJ内） | 「concreteスレ作って」「implementation新スレ」「`pj-flow thread <slug> <purpose>`」 |
| 4 | **Thread終了**（OUTPUT.md + pbcopy） | 「OUTPUT書いて」「Thread閉じて」「pbcopyして」 |
| 5 | **Project Close** | 「PJクローズ」「mergeした」「`closed_at`書いて」 |
| 6 | **In-flight adoption**（このスレを新規PJに昇格） | 「いまの会話をPJ化したい」「これPJ管理下に置きたい」 |
| 7 | **In-flight join**（このスレを既存PJに合流） | 「これ`<slug>`の作業だった」「`<slug>`に合流させて」 |
| 8 | **Import from artifacts**（外部成果物→PJ逆生成） | 「このPRからPJ作って」「Issue / Draft PR / branch から In Progress PJを起こして」 |
| 9 | **Migration**（旧PJ管理→pj-flow規約） | 「`my-projects/`をマイグレ」「`.claude/initiatives/`を取り込んで」 |
| 10 | **Self-improvement** | 「pj-flowここで止まらないで」「pbcopyのタイミング遅い」「SKILL更新して」 |

**判断不能なら2つまでに絞ってAskUserQuestionで確認**。「stopせず進めろ」セッションでは推測で進めてOKだが、不可逆操作（Migration / Close）は確認を挟む。

---

## 1. ロケーション規約

### 1.1 Project root の決定

デフォルトの保存先は repo 内の `.claude/my-projects/<slug>/` とする。Claude Code ではこの配置が最も自然で、既存の `CLAUDE.md` 文化とも相性がよい。

ただし、runner / repo 方針に応じてカスタムしてよい。AI は作業開始時に以下を自律判断する:

| 状況 | 推奨 root |
|---|---|
| Claude Code 中心、または既に `.claude/` がある | `.claude/my-projects/` |
| Codex / 複数 agent runtime で共有したい、または `.agents/` が既にある | `.agents/my-projects/` |
| ユーザーが保存先を明示した | ユーザー指定を最優先 |
| repo 内に private data を置けない | `$HOME/.agent-projects/<repo-slug>/my-projects/` 等の user scope |

以下の手順では `<PROJECTS_ROOT>` を使う。デフォルトは:

```bash
PROJECTS_ROOT="$REPO_ROOT/.claude/my-projects"
```

`.claude/my-projects/` または選択した `<PROJECTS_ROOT>` は、原則として `.gitignore` されている前提で扱う。PJ memory / thread output は private URL、顧客名、内部 issue、作業メモを含みやすい。チーム共有したい場合だけ、リポジトリ所有者の明示判断で tracking する。

新規PJ作成時は、書き込み前に `git check-ignore` で `<PROJECTS_ROOT>` 配下が ignore されているか確認する。

```bash
git check-ignore -q "$PROJECTS_ROOT/.probe"
```

- ignored ならそのまま進める。
- not ignored なら、いきなりPJファイルを書き始めない。ユーザーに「`<PROJECTS_ROOT>` が gitignore されていないため、private note が git 管理に入る可能性がある」と短く伝え、`.gitignore` 追加または user scope fallback のどちらで進めるか確認する。
- AI は `.gitignore` を勝手に書き換えない。ただしユーザーが「初回セットアップして」「gitignore して」等と明示した場合は、対象パターンを追加してよい。

```
<repo-root>/
└── .claude/
    └── my-projects/
        ├── <slug>/
        │   ├── CLAUDE.md                       # Project長期記憶（現時点スナップショット）
        │   └── threads/
        │       ├── YYYYMMDDHHMM-concrete/
        │       │   ├── OBJECTIVE.md
        │       │   ├── OUTPUT.md
        │       │   └── <assets...>
        │       └── YYYYMMDDHHMM-implementation/
        │           ├── OBJECTIVE.md
        │           ├── OUTPUT.md
        │           └── <assets...>
        └── <slug2>/...
```

- 旧 `my-projects/` 直下配置は **Migration対象**。原則として選択済み `<PROJECTS_ROOT>` に `git mv` で移す。手順: `references/migration-generic.md`。
- テンプレ実体は **このスキル内 `templates/`** に集約。各リポジトリにテンプレを置かない。
- 個人PJでもチームPJでも同じ規約。デフォルトは ignore。tracking は明示判断がある場合だけ。

### CLAUDE.md からの自動誘導は不要

旧運用は「ルートCLAUDE.mdに`my-projects/`を見るよう書く」だったが、**今後はこのスキルのトリガーで起動する**。CLAUDE.mdに参照を書き加える必要はない（書いてもよい）。

---

## 2. シナリオ別の手順

### 2.1 新規PJ立ち上げ（シナリオ#1）

```bash
# repo-root で実行
REPO_ROOT=$(git rev-parse --show-toplevel)
PROJECTS_ROOT="${PROJECTS_ROOT:-$REPO_ROOT/.claude/my-projects}"
SLUG=<kebab-case>        # 例: ai-tutor-free-release
mkdir -p "$PROJECTS_ROOT/$SLUG/threads"
cp "<pj-flow-skill-dir>/templates/project/CLAUDE.md" \
   "$PROJECTS_ROOT/$SLUG/CLAUDE.md"

# 起点 concrete Thread を切る
TS=$(TZ=Asia/Tokyo date +%Y%m%d%H%M)
cp -r "<pj-flow-skill-dir>/templates/thread-concrete" \
      "$PROJECTS_ROOT/$SLUG/threads/${TS}-concrete"
```

そのうえで:
1. `<slug>/CLAUDE.md` の frontmatter（slug / branch / issue_url / bundled_repos / created_at）を埋める
2. 本文（施策概要 / 背景 / スコープ / 非スコープ）を**現時点スナップショット**として書く
3. `threads/<TS>-concrete/OBJECTIVE.md` の「このThreadの目的」「調査観点」「Done定義」を埋める

**起点はconcreteから**を推奨。実装からいきなり始める場合は thread-implementation を使ってOKだが、後でreconcreteを足す覚悟をしておく。

### 2.2 既存PJ再開（シナリオ#2）

1. `<slug>/CLAUDE.md` を読む（現時点スナップショット）
2. `threads/` を `ls` して最新Threadを把握。最新の OUTPUT.md を読む
3. 「次に何をやるべきか」をユーザーに2〜3行で要約提示（最新OUTPUTの「次Threadへの引き継ぎ」「残作業」を起点に）
4. 新Threadが必要なら 2.3 へ。既存Threadの続きなら該当Threadのフォルダで作業

**自動的に最新Threadを「直前」として参照しない**（旧Ground Rule踏襲）。どのThreadを引き継ぐかは新Thread側で意識的に選ぶ。

### 2.3 Thread切り出し（シナリオ#3）

```bash
SLUG=<your-slug>
PURPOSE=concrete         # or implementation / reconcrete / spike / pivot / fix
TS=$(TZ=Asia/Tokyo date +%Y%m%d%H%M)
SYSTYPE=$([[ "$PURPOSE" =~ ^(implementation|pivot|fix)$ ]] && echo thread-implementation || echo thread-concrete)
cp -r "<pj-flow-skill-dir>/templates/$SYSTYPE" \
      "$PROJECTS_ROOT/$SLUG/threads/${TS}-${PURPOSE}"
```

purposeは自由語彙。よく使う: `concrete` / `implementation` / `reconcrete` / `spike` / `pivot` / `fix`。
**雛形は2系統のみ**（concrete系=情報収集 / implementation系=実装）。purposeに応じて中身を書き換える。

### 2.4 Thread終了 + pbcopy（シナリオ#4）

1. OUTPUT.md を **Done定義に従って書き切る**。曖昧な「だいたい書けた」では閉じない
2. 長期記憶の更新が必要なら `<slug>/CLAUDE.md` を上書きし `updated_at` を当日に更新
3. **次Threadキックオフプロンプトを pbcopy する**（テンプレは `references/pbcopy-prompts.md`）

pbcopy本文に前ThreadのOUTPUT要旨を**埋め込まない**（ドリフト防止）。参照パスだけ正確に列挙する。

### 2.5 Project Close（シナリオ#5）

PR が develop / main にマージされたら:
1. `<slug>/CLAUDE.md` frontmatter: `status: in_progress` → `closed`
2. `closed_at: YYYY-MM-DD`、`updated_at: 同日`
3. **ディレクトリは移動しない**（git履歴・pbcopy参照URLを壊さない）
4. 長期参照が不要になった旧PJは手動で `status: archived` に。**削除はしない**。

### 2.6 In-flight adoption（シナリオ#6） — このスレを新規PJに昇格

「いまの会話をPJ管理下に置きたい」と言われたとき:

1. ユーザーに `<slug>` を尋ねる（候補は会話のテーマから2案提示してAskUserQuestion）
2. 2.1 の手順で空PJを初期化（`branch` は現ブランチ、`issue_url`は分かれば埋める）。初期化前に `<PROJECTS_ROOT>` の ignore 状態を確認する
3. **会話の経緯から OBJECTIVE.md + OUTPUT.md を起こす**
   - これまでの調査・判断・実装結果を、起点Thread（`<TS>-concrete` or `<TS>-implementation`）の OUTPUT.md に**事後記入**する
   - 「Concrete系か Implementation系か」は会話の主成分で決める（コード書いてたなら implementation）
4. 長期記憶（CLAUDE.md）の「施策概要 / 背景 / スコープ」も会話から起こす
5. ユーザーに「この内容で確定でよいか」を1回確認

**事後Thread**であることを OUTPUT.md 冒頭に1行注記（例: `> このThreadは会話途中で adoption により事後生成された`）。

### 2.7 In-flight join（シナリオ#7） — このスレを既存PJに合流

「これ`<slug>`の作業だった」と言われたとき:

1. `<slug>/CLAUDE.md` を読み、現スコープと矛盾しないか確認
2. 矛盾するなら **長期記憶の更新が必要**な「中インパクト」案件。次 implementation Thread の OBJECTIVE に変更理由を記載
3. 新Threadを 2.3 で切り、いまの会話の成果を OUTPUT.md に事後記入
4. 「事後Thread」注記は同じく1行入れる

### 2.8 Import from artifacts（シナリオ#8） — PR/Issue/コード→In Progress PJ逆生成

「このPRからPJ作って」「Issueから In Progress PJを起こして」のとき。詳細手順: `references/import-from-artifacts.md`。

ざっくり:
1. **収集**: `gh pr view <url> --json title,body,headRefName,baseRefName,state,isDraft,commits,files` / `gh issue view` / Linear MCP / branch の `git log` で diff のサマリ
2. **slug 推定**: PR/Issue タイトルから kebab 化、ユーザー確認
3. **長期記憶起こし**: PRタイトル＋body→「施策概要」/ Issueの背景→「背景」/ 変更ファイル群→「スコープ」（推定）
4. **Thread 起こし**:
   - Draft PR / In Progress なら `<TS>-implementation`（事後）に変更ファイル一覧と現在の検証状況を反映
   - Issueのみ（コードなし）なら `<TS>-concrete`（事後）に背景・調査観点を反映
5. **未確定箇所は Open Questions に列挙**してから確認
6. ユーザーに「この内容で確定か」を確認

### 2.9 Migration（シナリオ#9） — 旧PJ管理→pj-flow

対応する旧フォーマット:
- `my-projects/` 直下方式 → `references/migration-generic.md`
- `.claude/initiatives/` 等の独自方式（1ファイル/1ディレクトリ）→ `references/migration-generic.md`
- **その他不明な独自方式** → `references/migration-generic.md`

Migration は **git mv ベース**で履歴を保つ。1コミット = 1PJ移行を原則とする。

### 2.10 Self-improvement（シナリオ#10） — スキル本体の改善

ユーザーが「pj-flowここで止まらないで欲しい」「pbcopyのタイミング遅い」等、**スキルの挙動への不満**を述べた場合:

1. 不満の本質を1行で言語化してユーザーに復唱（「○○のときに△△している、これを□□に変えるという理解で合っているか」）
2. 該当箇所を SKILL.md または references から特定
3. Edit で恒常化
4. 変更箇所と差分要約をユーザーに報告

**このスキルはグローバルに1つ**。どのリポジトリのスレッドからでも、同じファイルを編集することで全リポジトリに改善が波及する。

詳細・自己改善時のアンチパターン: `references/self-improvement.md`。

---

## 3. 仕様変更インパクトの3分類（旧運用踏襲）

| インパクト | 運用 |
|---|---|
| 小（挙動の微調整・命名変更） | 現Thread内 OUTPUT.md に注記して吸収。長期記憶は必要なら更新 |
| 中（機能スコープ追加削減・設計変更） | 次 implementation Thread のOBJECTIVE.mdに変更理由を明記。長期記憶を更新 |
| 大（前提が覆る・方針転換） | 新 `reconcrete` or `pivot` Threadを立てる。OBJECTIVE冒頭で **上書き対象の旧Thread** を明示。長期記憶を更新し `updated_at` を上げる |

旧OUTPUT.mdは**削除しない**（git履歴も残す）。過去経緯を追えるようにする。

---

## 4. 命名規約

### Project slug
- 任意のケバブケース短名
- Linear ID / GitHub Issue番号は slug に含めず、`<slug>/CLAUDE.md` の frontmatter に記録

### Thread フォルダ
- 形式: `YYYYMMDDHHMM-<purpose>`
- `YYYYMMDDHHMM` = Thread開始日時（JST、分まで）
- `<purpose>` 自由語彙。よく使う語彙はシナリオ#3を参照

最新Threadは `ls "$PROJECTS_ROOT/<slug>/threads/" | tail -1` で判る。

---

## 5. Project長期記憶 (`<slug>/CLAUDE.md`)

frontmatter 固定スキーマ:

```yaml
---
slug: <kebab-case>
status: in_progress          # in_progress | closed | archived
branch: feature/xxx-yyy
pr_url: null                 # PR作成後にURL
issue_url: <Linear or GitHub Issue URL>
bundled_repos: [server, client, app]   # 単一なら [client]
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD       # 本文を変更したら更新
closed_at: null              # Close時に YYYY-MM-DD
---
```

本文は **現時点スナップショット**（Projectの現在の真実）:
- 施策概要 / ゴール
- 背景 / 動機
- 現在のスコープ / 非スコープ
- 外部参照（Linear / esa / Slack 等）

仕様やスコープが変わったら **その場で上書き**する。変更履歴は git blame / git log で追う。
**実装進捗・Open Questions はここに書かない**（それらは各ThreadのOUTPUT.mdに置く）。

---

## 6. 全体一覧（grep one-liners）

Indexファイルは置かない。シェルで:

```bash
# アクティブPJ一覧（カレントrepo）
PROJECTS_ROOT="${PROJECTS_ROOT:-$(git rev-parse --show-toplevel)/.claude/my-projects}"
grep -l '^status: in_progress' "$PROJECTS_ROOT"/*/CLAUDE.md | xargs -I{} dirname {}

# PR未作成
grep -l '^pr_url: null' "$PROJECTS_ROOT"/*/CLAUDE.md

# Bundled repo別
grep -l 'server' "$PROJECTS_ROOT"/*/CLAUDE.md

# 任意の workspace root 配下を横断
find "$WORKSPACE_ROOT" -maxdepth 5 -type d -name "my-projects" 2>/dev/null
```

---

## 7. トライアル・グラデーション（不可逆要素を含むタスクで適用）

「採用する／しない」の二項対立で意思決定を提示しない。試行段階を 3〜8 レベルに分解、各レベル終了時に「次へ進める / 止める」を毎回判断する。最終採用まで一気通貫の plan を出さない。

### 適用するタスクの形質
- 本番環境への副作用が発生しうる
- credential revoke / branch protection 変更 / 公開リリース等の不可逆要素を含む
- 実機で挙動を見ないと最終判断できない仮説検証

### 文書化先
該当Threadの `docs/` 配下に `<番号>-trial-gradient.md` で配置し、OUTPUT.md から index する。
列構成: 「ロールバックコスト / 得られる情報 / 不可逆ポイント」

---

## 8. このスキルが**やらないこと**

- `/project-kickoff` 系の Claude Code custom command と機能統合**しない**（別系統として共存）
- 各リポジトリのルート CLAUDE.md を勝手に書き換え**ない**（Migration時にのみ提案）
- `.gitignore` を勝手にいじら**ない**（ただし、初回セットアップや gitignore 追加を明示された場合は実施してよい）
- 旧 OUTPUT.md / 旧 Threadフォルダを **削除しない**
- 「直前Thread」を自動的に新Threadの参照Threadに**しない**（明示的に選ぶ）

---

## 9. references/ 索引

- `references/pbcopy-prompts.md` — Thread終了時のpbcopyテンプレ集
- `references/migration-generic.md` — 不明な独自方式からのマイグレ
- `references/import-from-artifacts.md` — PR/Issue/コードからのPJ逆生成
- `references/in-flight-adoption.md` — 途中昇格・途中合流のディテール
- `references/self-improvement.md` — スキル自己改善の運用

---

## 10. このスキルの命名と所在を変えるとき

runner のスキル配置で `pj-flow/` を別名にする / 場所を変えるときは:
1. このスキルを呼び出している箇所がほぼ無い前提（外部リファレンスが少ない）
2. 複数 runtime に symlink している場合はすべて張り直す
3. references 内のパス記述を全て一括置換
