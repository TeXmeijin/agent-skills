# Agent Skills

Claude Code、Codex、その他 Agent Skills のディレクトリ構成に対応した実行環境で使うための汎用スキル集です。

このリポジトリは APM package として、次の形式でスキルを配置しています。

```text
.apm/skills/<skill-name>/SKILL.md
```

## スキル一覧
### 日常利用
- `commit-push` - このスレッドで変更したファイルだけを commit / push する。
- `non-committed-analyzer` - 未コミット変更を読み、コミット分割案や検証手順を出す。
- `ggg` - 最新性が重要な質問で Web 検索に基づいて回答するように強制する。
- `isis` - Issue やチケットを実装前の仮説として調査・整理する。
- `goal-template-generator` - ラフな依頼を、実行可能な GOAL テンプレートに整える。
- `codex-exec` - Codex CLI に rescue / review タスクを委譲する。
- `codex-collab-review` - Claude Code と Codex CLI で協働レビューを行う。
- `prompt-refiner` - 雑な coding 依頼を、別の agent に渡せる prompt に整える。

### 特定のタスク
- `ghostty-applescript` - Ghostty の AppleScript レイアウトを作成する。
- `cloudwatch-logs-insights-query` - CloudWatch Logs Insights QL のクエリを作成・検証する。
- `yarn-classic-to-pnpm` - Yarn Classic から pnpm への移行や依存バージョン差分を監査する。
- `harness-creator` - Red/Green を機械判定できる検証ハーネスを作る。

## APM でインストール

```sh
apm install TeXmeijin/agent-skills --target agent-skills,claude,codex
```

ユーザースコープにインストールする場合:

```sh
apm install -g TeXmeijin/agent-skills --target agent-skills,claude,codex
```

## ローカル開発

ローカルで編集する場合は、このリポジトリを source of truth にして、各実行環境のスキル配置先へ symlink します。

```sh
./scripts/link-local.sh
```

このスクリプトは、既存の実ディレクトリをバックアップしてから symlink に置き換えます。
