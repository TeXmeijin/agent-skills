# Agent Skills

個人的によく使っている自作スキルのうち、外部公開できそうなものをまとめています。

このリポジトリは APM package として、次の形式でスキルを配置しています。

```text
.apm/skills/<skill-name>/SKILL.md
```

## スキル一覧
### プロジェクト管理
- `pj-flow` - `.claude/my-projects/` に長期記憶と Thread を積んで、長いPJを会話スレッドをまたいで継続できるようにする。新スレッドでもすぐにAgentがPJの目的、背景、最新情報などを把握してくれるので、説明負荷が下がる。外部ツールとの連携も不要のため高速に動作する。

### ちょっとした作業
- `commit-push` - このスレッドで変更したファイルだけを commit / push する。
- `non-committed-analyzer` - 未コミット変更を読み、コミット分割案や検証手順を出す。気がつけばコミットせずに大量の作業をしていたときに使う。

### よりAgentに明確な指示を出す
- `ggg` - 最新性が重要な質問で Web 検索に基づいて回答するように強制する。Web検索をサボってきたときに使う。
- `goal-template-generator` - ラフな依頼を、実行可能な GOAL テンプレートに整える。`/goal`コマンドを次スレッドで使うための下準備。
- `isis` - Issue やチケットを実装前の仮説として調査・整理する。
- `harness-creator` - Red/Green を機械判定できる検証ハーネスを作る。
- `prompt-refiner` - 雑な coding 依頼を、別の agent に渡せる prompt に整える。goalの下位互換かも...

### Claude CodeからCodexに連携
- `codex-exec` - Codex CLI に rescue / review タスクを委譲する。
- `codex-collab-review` - Claude Code と Codex CLI で協働レビューを行う。

### UIデザイン
- `centering-judge` - 画像の整列 (中央揃え / 左端揃え / 間隔均等 等) を画素単位で判定するスクリプトを、 命題ごとに新規実装して走らせる skill。LLM の主観で「揃ってる」と誤判定するのを防ぐためのメタ手法。 固定スクリプトは持たず、 共通道具箱 (背景マスク / content profile / debug overlay 等) と参考実装を提供する。

### 特定のタスク
- `ghostty-applescript` - Ghostty 対応のレイアウトを AppleScript で実装する。
- `cloudwatch-logs-insights-query` - CloudWatch Logs Insights QL のクエリを作成・検証する。
- `yarn-classic-to-pnpm` - Yarn Classic から pnpm v11+ への移行をしつつ、依存バージョン差分を監査して、Patch Versionに至るまでバージョン差異を報告する。

## APM でインストール

```sh
apm install TeXmeijin/agent-skills --target agent-skills,claude,codex
```

ユーザースコープにインストールする場合:

```sh
apm install -g TeXmeijin/agent-skills --target agent-skills,claude,codex
```

個別のスキルだけをインストールする場合:

```sh
apm install -g TeXmeijin/agent-skills --skill pj-flow --target agent-skills,claude,codex
```

複数のスキルを選ぶ場合:

```sh
apm install -g TeXmeijin/agent-skills \
  --skill pj-flow \
  --skill codex-exec \
  --target agent-skills,claude,codex
```

すべてのスキルに戻す場合:

```sh
apm install -g TeXmeijin/agent-skills --skill '*' --target agent-skills,claude,codex
```

## ローカル開発

ローカルで編集する場合は、このリポジトリを source of truth にして、各実行環境のスキル配置先へ symlink します。

```sh
./scripts/link-local.sh
```

このスクリプトは、既存の実ディレクトリをバックアップしてから symlink に置き換えます。
