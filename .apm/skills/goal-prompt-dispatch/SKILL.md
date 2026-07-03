---
name: goal-prompt-dispatch
description: "貯めておいた高品質GOALプロンプトを、後で高性能モデルにまとめて処理するためのランナー。goal-prompt-enqueue がキュー(~/.goal-prompt-queue/inbox/)に積んだGOALを、1回の起動につき最大1件だけ取り出し、記憶ゼロ前提でそのGOALを自律実行する。inbox → inprogress → done/error の4フォルダで競合を避ける。『貯めたGOALを実行して』『dispatchして』『キューを1件回して』『inboxのGOALを実行して』と言われたとき、または定時トリガー(cron/schedule)から呼ばれたときに使う。Claude / Codex など任意のagentから実行できる。"
disable-model-invocation: true
user-invocable: true
---

# Goal Prompt Dispatch

気合を入れた高品質GOALプロンプトを貯めておき、後で高性能モデルにまとめて実行させる——このフローの「実行する側」。`goal-prompt-enqueue` が積んだGOALファイルを1件取り出して実行する、対になるランナー。

このskillは**副作用（コミット・PR作成・ファイル移動）を持つ**ため、会話の流れで勝手に発火しない設定（`disable-model-invocation: true`）にしている。定時トリガーからの起動、または明示的な `/goal-prompt-dispatch` 呼び出しでのみ動く。

## 前提: このランナーは記憶ゼロで起動される

このskillは毎回、会話の記憶を持たない新規セッションから起動される想定。「前回」「さっき話した」といった文脈は一切ない。この手順とGOALファイル本文だけを根拠に判断する。

## キューの場所と4フォルダの意味

キュー実体:

```
~/.goal-prompt-queue/
├── inbox/       未処理のGOALファイル
├── inprogress/  実行中（1件をここへ移した時点で「掴んだ」ことになる）
├── done/        正常終了（DONE WHEN到達 / PR作成 / 意図した停止）
└── error/       異常終了（要人間確認: 復旧不能な失敗・認証切れ・想定外STOP）
```

このキューがホーム直下にあるのは、enqueue と dispatch を Claude / Codex どちらから呼んでも同じ実体を指すようにするため（skill 配下だと呼び出した agent ごとに別ディレクトリになり取りこぼす）。

`inbox → inprogress → done/error` の4段階は**競合回避のための設計**。二重実行を防ぐのは「選定直後に `inprogress/` へ原子的に移す」ことだけで足りる（同一ファイルシステム上の `mv` は原子的で、2つ目のランナーが同じファイルを掴もうとすると「元ファイルが無い」で失敗する）。逆に言えば、`inprogress/` に別の処理中ファイルがあっても新規起動をブロックしない — それは別ファイルなので、このランナーは inbox から自分の1件を掴んで並行に進めてよい。クラッシュで `inprogress/` に取り残されたファイルは、このランナーが自動で奪い返さず、人間が `inbox/` へ戻すか `error/` へ振り分ける。

## 実行手順

以下を上から順に実行する。1回の起動で処理するGOALは**最大1件**。

### 1. inbox が空なら終了

```bash
Q="$HOME/.goal-prompt-queue"
ls "$Q"/inbox/*.md >/dev/null 2>&1 || { echo "inboxに処理対象なし"; exit 0; }
```

### 2. 最古1件を選び、inprogress へ原子的に移す（競合ガード）

frontmatter の `created_at` が最も古い1件を選ぶ。同日ならファイル名の昇順。選んだら**他の操作をする前に**すぐ `inprogress/` へ移す。`mv` が失敗したら別ランナーが先に掴んだということなので、何もせず終了する（無理に次の候補を掴みにいかず、次回の起動に委ねる）。

```bash
F=$(for f in "$Q"/inbox/*.md; do
      ca=$(awk -F': *' '/^created_at:/{print $2; exit}' "$f")
      printf '%s\t%s\n' "$ca" "$f"
    done | sort | head -1 | cut -f2-)
BN=$(basename "$F")
mv "$F" "$Q/inprogress/$BN" || { echo "別ランナーが先に掴んだため終了"; exit 0; }
INPROG="$Q/inprogress/$BN"
```

以降、処理対象はこの `inprogress/` 内の1件のみ。inbox の他ファイルには一切触れない。

### 3. workspace_directory へ移動し、本文をGOALとして実行

`inprogress/` に移したファイルの frontmatter から `workspace_directory` を読み、そのディレクトリへ `cd` する。frontmatter 以降の本文全体を、そのプロジェクトに対する実行すべきGOALとして扱う。

- `/goal` コマンドは Claude / Codex いずれにもある。使える環境なら本文を `/goal` に渡して実行する。
- 何らかの理由で `/goal` が使えない環境なら、本文をそのままタスクブリーフとして直接実行する。

本文中の **CONSTRAINTS / DONE WHEN / VERIFY / STOP RULES は必ず遵守する**。GOAL本文は実行体制（実装は経済ティアのサブエージェントに委譲し、メインは最上位モデルで計画・危険操作判断・レビューに専念）を指定している。サブエージェントのモデルはこのランナー自身の実行プラットフォームに対応付ける — **Claudeで実行しているならサブエージェントは Sonnet を指定する**（`model: 'sonnet'`）、Codexで実行しているなら相応の経済ティアを使う。

軽微な判断は自律的に進めてよい。ただし本文の STOP RULES に該当する事態が起きたら直ちに止める。プロジェクトの既定マージ先（develop 等）向けの PR を作成した時点で、それ以上の作業はせず停止する（STOP RULE が先に該当した場合はその時点で停止）。

### 4. 終了処理（done / error へ振り分け、completed_at と結果を追記）

作業が終わったら、`inprogress/` のファイルを `done/` または `error/` へ移す。振り分けの目安:

- **done**: DONE WHEN を満たした / 既定マージ先向け PR を作成した / GOAL が想定した安全な停止点で止まった。
- **error**: 復旧不能な失敗、認証切れで安全な停止点に到達できなかった、想定外の STOP RULE 発動（worktree が dirty、対象 PR が既にマージ済み等、人間の確認が要る状態）。

どちらの場合も、移動先ファイルの frontmatter に `completed_at`（`date '+%Y-%m-%d %H:%M'`）と、1〜2行の結果サマリ（PRリンク or 停止理由）を追記する。

```bash
# 例: done へ（frontmatter の末尾 --- の直前に追記する形で編集する）
mv "$INPROG" "$Q/done/$BN"
```

frontmatter への追記は、既存の `title` / `workspace_directory` / `created_at` を壊さず、`completed_at:` と `result: |` を足す（enqueue 側は生成時にこれらを書かない約束なので、必ず未記入の状態から足せる）。

### 5. 完了報告

1回の起動につき最大1件という原則を守り、2件目以降には手を出さない。報告には、処理したファイル名（またはスキップ理由）と、PRリンク（あれば）を含める。

## 認証・権限が切れているとき

GitHub 認証（`gh auth status`）が切れている、push 権限が無い等でリモート操作ができない場合は、**ローカルのブランチ/コミットまでで止める**。無理に進めず、その時点の状態を `result` に明記して `error/`（または本文の STOP RULES が「ローカルコミットで停止」を許容していれば `done/`）へ移す。PR 用のタイトル・本文案を `result` に残しておくと次に拾いやすい。

## 定時トリガーからの起動

このskillは cron / scheduled task から発火される想定。トリガー側のプロンプトは、記憶ゼロ前提を明示した上で、Claude なら `/goal-prompt-dispatch` を呼ぶ、Codex なら本skillの手順に従う、と指示するだけでよい（手順の実体はこのファイルが持つ）。スケジュール登録自体（`schedule` skill や OS の cron）はこのskillのスコープ外。
